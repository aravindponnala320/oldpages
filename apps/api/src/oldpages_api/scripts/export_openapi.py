from __future__ import annotations

import json

from oldpages_api.main import create_app


def main() -> None:
    app = create_app()
    print(json.dumps(app.openapi(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
