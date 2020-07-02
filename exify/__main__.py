import asyncio

from loguru import logger

from exify.analyzer.image_analyzer import WhatsappImageAnalyzer
from exify.errors import ExifyError
from exify.models import FileItem
from exify.settings import get_settings, ExifySettings, configure_logging
from exify.writer.file_metadata_writer import FileTimestampWriter
from exify.writer.exif_timestamp_writer import ExifTimestampWriter


def expand_to_absolute_path(file):
    if not file.is_absolute():
        file = get_settings().base_dir / file
    assert file.exists(), f'{file} does not exist'
    return file.absolute()


def is_whatsapp_file(filename):
    return 'WA' in filename.name


def is_image(filename):
    return filename.suffix.lower() in ('.jpg', '.jpeg')


async def run(settings: ExifySettings):
    logger.info(f'Settings: {settings}')

    ok = []
    updated = []
    errors = []

    for file in await _find_files(settings.base_dir):
        filename = expand_to_absolute_path(file)

        if not is_whatsapp_file(filename) or not is_image(filename):
            continue

        item = FileItem(
            file=filename
        )

        try:
            item = await _analyze_file(item, settings)
        except ExifyError as err:
            item.errors.append(err)
            errors.append(item)
        if await _all_ok(item.results):
            ok.append(item)
        else:
            try:
                if not item.results.exif_timestamp_exists:
                    await _write_exif_data(item)
                if not item.results.deviation_ok:
                    await _write_file_time_stamp(item)
                updated.append(item)
            except ExifyError as err:
                item.errors.append(err)
                errors.append(item)

    logger.info(f'OK: {len(ok)}, UPDATED: {len(updated)}, ERRORS: {len(errors)}')

    for failed in errors:
        logger.warning(f'Process failed for {failed.file}: {failed.errors}')


async def _all_ok(item_results):
    return item_results.exif_timestamp_exists and item_results.deviation_ok


async def _find_files(src):
    files = [x for x in src.rglob('*') if x.is_file()]
    return files


async def _write_exif_data(item):
    await ExifTimestampWriter(item).write()


async def _write_file_time_stamp(item):
    await FileTimestampWriter(item).write()


async def _analyze_file(item: FileItem, settings: ExifySettings):
    await WhatsappImageAnalyzer(item, settings=settings).run()
    logger.debug(f'{item.file}: {item.results}')
    return item


if __name__ == '__main__':
    configure_logging()
    settings = get_settings()
    asyncio.run(run(settings=settings))
