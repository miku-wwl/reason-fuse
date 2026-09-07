"""Hosted Agent entry point; keep src on the import path for remote builds."""

import asyncio

from reasonfuse.main import main


if __name__ == "__main__":
    asyncio.run(main())
