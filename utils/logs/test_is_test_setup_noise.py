from utils.logs.is_test_setup_noise import is_test_setup_noise


def test_objectid_lines():
    assert is_test_setup_noise('Application: new ObjectId("603818c2d2e5bf000745ff49"),')
    assert is_test_setup_noise('new ObjectId("60381a6da9ff7000084a07c0")')


def test_mongo_config():
    assert is_test_setup_noise("Using default value 10 for maxPoolSize")
    assert is_test_setup_noise(
        "Connected to MongoDB (maxPoolSize: 10, maxIdleTimeMS: 10000)"
    )
    assert is_test_setup_noise(
        "[EMFILE investigation] Starting investigation in 2026/04/14/pr-agent-prod"
    )
    assert is_test_setup_noise("*** new process, emfiles count: 27")
    assert is_test_setup_noise("stage is undefined")


def test_seed_data():
    assert is_test_setup_noise(
        "E&C: Application inserted with id: 69de42fdc97e3218b3fa49ac"
    )
    assert is_test_setup_noise(
        "inserted ActivePolicy with id: 69de42fdc97e3218b3fa49b4"
    )
    assert is_test_setup_noise("Payment was removed")
    assert is_test_setup_noise("PolicyPaymentSchedule was removed")


def test_entity_field_warnings():
    assert is_test_setup_noise("No such field in flow or policy - Payment")
    assert is_test_setup_noise(
        "No such field in policy when insert id into policy - PolicyPaymentSchedule"
    )


def test_business_data():
    assert is_test_setup_noise("policy number: P20210225V3OS69")
    assert is_test_setup_noise("invoice number: I20210225R8COV3")
    assert is_test_setup_noise("quoteNumber: Q20210225BB3RKN")
    assert is_test_setup_noise(
        "getIds for issues appear in the data review, P20211103KV64DU's latest ids are"
    )


def test_migration_files():
    assert is_test_setup_noise(
        "'20220505134722-manual-cancellation-P202203047MQ1YA.js',"
    )
    assert is_test_setup_noise(
        "'20220720162306-manual-cancellation-P20220405B0MMUB.js'"
    )


def test_numeric_ids():
    assert is_test_setup_noise("17645612")
    assert is_test_setup_noise("18839777")


def test_array_truncation():
    assert is_test_setup_noise("... 18 more items")


def test_brackets():
    assert is_test_setup_noise("{")
    assert is_test_setup_noise("}")
    assert is_test_setup_noise("[")
    assert is_test_setup_noise("]")
    assert is_test_setup_noise("],")


def test_aws_metadata():
    assert is_test_setup_noise("'$fault': 'client',")
    assert is_test_setup_noise("'$metadata': {")
    assert is_test_setup_noise("httpStatusCode: 400,")
    assert is_test_setup_noise("requestId: '0783164c-dc8a-48df-97d7-dffd9d3e9f78',")
    assert is_test_setup_noise("__type: 'AccessDeniedException'")


def test_yarn_noise():
    assert is_test_setup_noise(
        "info Visit https://yarnpkg.com/en/docs/cli/run for documentation about this command."
    )
    assert is_test_setup_noise(
        'warning From Yarn 1.0 onwards, scripts don\'t require "--"'
    )


def test_node_deprecation():
    assert is_test_setup_noise(
        "(node:1966) [DEP0040] DeprecationWarning: The `punycode` module is deprecated."
    )
    assert is_test_setup_noise(
        "(Use `node --trace-deprecation ...` to show where the warning was created)"
    )


def test_ssm_fetch_fallback():
    assert is_test_setup_noise(
        "Failed to fetch maxPoolSize from SSM, falling back to default: 10 AccessDeniedException"
    )


def test_entity_array_headers():
    assert is_test_setup_noise("ApplicationAnswers: [")
    assert is_test_setup_noise("migrated: [")


def test_error_in_mongodb_operation():
    assert is_test_setup_noise("Error in MongoDB operation:")


def test_not_noise():
    assert not is_test_setup_noise("FAIL src/test.ts")
    assert not is_test_setup_noise("  ✕ should work (5 ms)")
    assert not is_test_setup_noise("error Command failed with exit code 1.")
    assert not is_test_setup_noise(
        "AccessDeniedException: User: arn:aws:sts::948023073771"
    )
    assert not is_test_setup_noise(
        "    at process.processTicksAndRejections (node:internal/process/task_queues:103:5)"
    )
    assert not is_test_setup_noise("Test Suites: 1 failed, 1 total")
    assert not is_test_setup_noise("yarn run v1.22.22")
    assert not is_test_setup_noise("$ jest --findRelatedTests src/test.ts")
