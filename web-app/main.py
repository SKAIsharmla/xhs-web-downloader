# Copyright (C) 2025 SKAIsharmla
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import uvicorn

from config import WebConfig

if __name__ == "__main__":
    cfg = WebConfig().load()
    uvicorn.run(
        "server:app",
        host=cfg.get("server_host", "0.0.0.0"),
        port=cfg.get("server_port", 8080),
        reload=False,
        log_level="info",
    )
