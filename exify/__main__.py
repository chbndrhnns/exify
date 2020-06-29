import asyncio
from collections import defaultdict
from typing import List

from loguru import logger

from exify.analyzer.whatsapp_analyzer import WhatsappFileAnalyzer
from exify.models import ExifySettings, FileItem
from exify.settings import get_settings


def _expand_to_absolute_path(file):
    if not file.is_absolute():
        file = get_settings().base_dir / file
    return file.absolute()


async def run(settings: ExifySettings):
    src = settings.base_dir
    logger.info(f'Running on {src}...')

    if files := [x for x in src.iterdir() if x.is_file()]:
        results = await analyze_files(files, settings)
        await analyze_results(results)


async def analyze_results(items: List[FileItem]):
    ok = []
    not_ok = []
    for item in items.values():
        if any([res for res in item.results]):
            not_ok.append(item)
        else:
            ok.append(item)

    logger.info(f'OK: {len(ok)}')
    logger.info(f'NOT OK: {len(not_ok)}')


async def analyze_files(files, settings):
    results = defaultdict(FileItem)
    for filename in files:
        filename = _expand_to_absolute_path(filename)
        item = FileItem(
            file=filename
        )
        results[filename] = item

        await WhatsappFileAnalyzer(item, settings=settings).analyze_timestamp()
        logger.info(f'{filename}: {item.results}')
    return results


if __name__ == '__main__':
    settings = get_settings()
    asyncio.run(run(settings=settings))
