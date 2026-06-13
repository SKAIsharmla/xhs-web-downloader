/* ========================================================================
   小红书图片下载器 — Frontend Logic
   ======================================================================== */

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // DOM refs
  // -----------------------------------------------------------------------
  const urlInput        = document.getElementById("urlInput");
  const parseBtn        = document.getElementById("parseBtn");
  const statusArea      = document.getElementById("statusArea");
  const resultPanel     = document.getElementById("resultPanel");

  const postType        = document.getElementById("postType");
  const postAuthor      = document.getElementById("postAuthor");
  const postTime        = document.getElementById("postTime");
  const postLikes       = document.getElementById("postLikes");
  const postTitle       = document.getElementById("postTitle");
  const postDesc        = document.getElementById("postDesc");

  const selectAll       = document.getElementById("selectAll");
  const selectInfo      = document.getElementById("selectInfo");
  const downloadBtn     = document.getElementById("downloadBtn");
  const imageGrid       = document.getElementById("imageGrid");

  const progressArea    = document.getElementById("progressArea");
  const progressFill    = document.getElementById("progressFill");
  const progressText    = document.getElementById("progressText");

  const settingsBtn     = document.getElementById("settingsBtn");
  const settingsModal   = document.getElementById("settingsModal");
  const modalClose      = document.getElementById("modalClose");

  const setDownloadDir  = document.getElementById("setDownloadDir");
  const setImageFormat  = document.getElementById("setImageFormat");
  const setAuthorArchive= document.getElementById("setAuthorArchive");
  const setCookie       = document.getElementById("setCookie");
  const saveSettingsBtn = document.getElementById("saveSettingsBtn");

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  let currentImages = [];          // { index, url, live_url }[]
  let currentUrl    = "";          // original URL from last parse
  let isDownloading = false;

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------
  function showStatus(msg, type) {
    statusArea.classList.remove("hidden", "success", "error", "loading");
    statusArea.textContent = msg;
    statusArea.classList.add(type);
  }

  function hideStatus() {
    statusArea.classList.add("hidden");
  }

  function showLoading(msg) {
    showStatus(msg || "处理中...", "loading");
  }

  function showSuccess(msg) {
    showStatus(msg, "success");
  }

  function showError(msg) {
    showStatus(msg, "error");
  }

  function toggleBtn(btn, disabled) {
    btn.disabled = disabled;
  }

  function formatTime(timeStr) {
    if (!timeStr || timeStr === "未知") return timeStr;
    // The backend returns YYYY-MM-DD_HH:MM:SS
    return timeStr.replace(/_/, " ");
  }

  // -----------------------------------------------------------------------
  // API calls
  // -----------------------------------------------------------------------
  async function apiPost(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  }

  async function apiGet(url) {
    const res = await fetch(url);
    return res.json();
  }

  // -----------------------------------------------------------------------
  // Parse
  // -----------------------------------------------------------------------
  async function handleParse() {
    const url = urlInput.value.trim();
    if (!url) {
      showError("请先粘贴小红书链接");
      return;
    }

    hideStatus();
    showLoading("正在解析链接...");
    toggleBtn(parseBtn, true);

    try {
      const json = await apiPost("/api/parse", { url });

      if (!json.success) {
        showError(json.message || "解析失败");
        resultPanel.classList.add("hidden");
        return;
      }

      showSuccess(json.message);
      renderPostInfo(json.data);
      renderImages(json.data.图片列表 || []);
      currentImages = json.data.图片列表 || [];
      currentUrl = url;
      resultPanel.classList.remove("hidden");
      updateSelectInfo();
    } catch (err) {
      showError("网络错误：" + err.message);
      resultPanel.classList.add("hidden");
    } finally {
      toggleBtn(parseBtn, false);
    }
  }

  // -----------------------------------------------------------------------
  // Render post info
  // -----------------------------------------------------------------------
  function renderPostInfo(data) {
    postType.textContent  = data.作品类型 || "未知";
    postAuthor.textContent = data.作者昵称 || "未知";
    postTime.textContent  = formatTime(data.发布时间);
    postLikes.textContent = `❤ ${data.点赞数量 || "0"}`;
    postTitle.textContent = data.作品标题 || "(无标题)";
    postDesc.textContent  = data.作品描述 || "";
  }

  // -----------------------------------------------------------------------
  // Render image grid
  // -----------------------------------------------------------------------
  function renderImages(images) {
    imageGrid.innerHTML = "";

    if (!images || images.length === 0) {
      imageGrid.innerHTML = '<div class="card" style="grid-column:1/-1;text-align:center;color:#999;">未找到图片</div>';
      return;
    }

    images.forEach((img) => {
      const card = document.createElement("div");
      card.className = "image-card selected";
      card.dataset.index = img.index;

      const indexBadge = document.createElement("span");
      indexBadge.className = "image-index";
      indexBadge.textContent = img.index;

      const checkMark = document.createElement("span");
      checkMark.className = "image-check";
      checkMark.textContent = "✓";

      const imgEl = document.createElement("img");
      imgEl.alt = `图片 ${img.index}`;
      imgEl.loading = "lazy";

      // Use proxy endpoint for reliable loading
      imgEl.src = `/api/image?url=${encodeURIComponent(img.url)}`;
      imgEl.onerror = function () {
        // Fallback: try direct CDN URL
        this.src = img.url;
      };
      imgEl.onerror = function () {
        // Last resort
        this.outerHTML = `<div class="image-placeholder">图片 ${img.index}<br>加载失败</div>`;
      };

      card.appendChild(indexBadge);
      card.appendChild(checkMark);
      card.appendChild(imgEl);

      card.addEventListener("click", () => {
        card.classList.toggle("selected");
        updateSelectInfo();
      });

      imageGrid.appendChild(card);
    });

    selectAll.checked = true;
  }

  // -----------------------------------------------------------------------
  // Selection helpers
  // -----------------------------------------------------------------------
  function getSelectedIndices() {
    const indices = [];
    document.querySelectorAll(".image-card.selected").forEach((card) => {
      indices.push(parseInt(card.dataset.index, 10));
    });
    return indices.sort((a, b) => a - b);
  }

  function updateSelectInfo() {
    const sel = getSelectedIndices();
    selectInfo.textContent = `已选择 ${sel.length} / ${currentImages.length} 张图片`;
  }

  // Select all / none
  selectAll.addEventListener("change", () => {
    const checked = selectAll.checked;
    document.querySelectorAll(".image-card").forEach((card) => {
      card.classList.toggle("selected", checked);
    });
    updateSelectInfo();
  });

  // -----------------------------------------------------------------------
  // Download
  // -----------------------------------------------------------------------
  async function handleDownload() {
    if (isDownloading) return;

    const indices = getSelectedIndices();
    if (indices.length === 0) {
      showError("请先选择要下载的图片");
      return;
    }

    if (!currentUrl) {
      showError("请先解析链接");
      return;
    }

    isDownloading = true;
    toggleBtn(downloadBtn, true);
    progressArea.classList.remove("hidden");
    progressFill.style.width = "0%";
    progressText.textContent = `正在下载 ${indices.length} 张图片...`;
    hideStatus();

    try {
      const json = await apiPost("/api/download", {
        url: currentUrl,
        index: indices,
      });

      if (json.success) {
        progressFill.style.width = "100%";
        progressText.textContent = `下载完成！共 ${json.data?.下载数量 || indices.length} 张图片已保存到服务器`;
        showSuccess(json.message);
      } else {
        progressText.textContent = "下载失败";
        showError(json.message || "下载失败");
      }
    } catch (err) {
      progressText.textContent = "网络错误";
      showError("网络错误：" + err.message);
    } finally {
      isDownloading = false;
      toggleBtn(downloadBtn, false);
    }
  }

  // -----------------------------------------------------------------------
  // Settings
  // -----------------------------------------------------------------------
  async function openSettings() {
    settingsModal.classList.remove("hidden");
    try {
      const json = await apiGet("/api/settings");
      if (json.success) {
        setDownloadDir.value   = json.data.download_dir || "";
        setImageFormat.value   = json.data.image_format || "jpeg";
        setAuthorArchive.checked = json.data.author_archive || false;
        // We don't fetch the actual cookie value back for security,
        // just show whether one is set
        if (json.data.has_cookie) {
          setCookie.placeholder = "已设置 Cookie（输入新值覆盖，留空保持不变）";
        } else {
          setCookie.placeholder = "从浏览器 F12 → Application → Cookies 复制";
        }
      }
    } catch (err) {
      // silently fail - user can still see current values
    }
  }

  function closeSettings() {
    settingsModal.classList.add("hidden");
  }

  async function saveSettings() {
    const body = {
      download_dir:  setDownloadDir.value.trim() || undefined,
      image_format:  setImageFormat.value,
      author_archive: setAuthorArchive.checked,
    };
    const cookieVal = setCookie.value.trim();
    if (cookieVal) {
      body.cookie = cookieVal;
    }

    try {
      const json = await apiPost("/api/settings", body);
      if (json.success) {
        showSuccess("设置已保存");
        closeSettings();
      } else {
        showError(json.message || "保存设置失败");
      }
    } catch (err) {
      showError("网络错误：" + err.message);
    }
  }

  // -----------------------------------------------------------------------
  // Event bindings
  // -----------------------------------------------------------------------
  parseBtn.addEventListener("click", handleParse);

  urlInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleParse();
  });

  downloadBtn.addEventListener("click", handleDownload);

  settingsBtn.addEventListener("click", openSettings);
  modalClose.addEventListener("click", closeSettings);
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) closeSettings();
  });
  saveSettingsBtn.addEventListener("click", saveSettings);

  // -----------------------------------------------------------------------
  // Init: focus input
  // -----------------------------------------------------------------------
  urlInput.focus();

})();
