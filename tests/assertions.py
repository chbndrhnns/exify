async def generated_timestamp_matches_file_name_timestamp(analyzer, writer):
    actual = writer.generated_timestamp
    expected = analyzer.authoritative_timestamp_attribute
    assert (actual.year, actual.month, actual.day) == (expected.year, expected.month, expected.day)


async def file_timestamp_matches_generated_timestamp(analyzer, writer):
    await analyzer.gather_timestamp_data()
    await writer.generate_timestamp()

    assert analyzer._item.timestamps.file_modified == writer.item.timestamps.file_modified, \
        'file_modified not as expected'
    assert analyzer._item.timestamps.file_created == writer.item.timestamps.file_created, \
        'file_created not as expected'
