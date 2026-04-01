from pathlib import Path

from utils.files.find_test_files import find_test_files

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(repo_name: str):
    return (FIXTURES_DIR / f"{repo_name}.txt").read_text().strip().split("\n")


# ---- Edge case tests (minimal data by nature) ----


def test_empty_stem():
    assert not find_test_files("", [], None)


def test_partial_stem_no_match():
    # "generate" != "generateId" - exact stem match rejects partial matches
    all_files = ["src/utils/generate.ts", "src/utils/generateId.test.ts"]
    assert not find_test_files("src/utils/generate.ts", all_files, None)


def test_non_test_file_with_matching_name():
    all_files = ["src/utils/generateId.ts", "src/utils/generateId.utils.ts"]
    assert not find_test_files("src/utils/generateId.ts", all_files, None)


# ---- Real repo tests (full git ls-files fixtures) ----


def test_real_foxcom_forms():
    # foxcom-forms: 389 files. Jest colocated .test.tsx pattern.
    all_files = _load_fixture("foxcom-forms")
    assert len(all_files) > 300
    assert find_test_files("src/auth/AuthProvider.tsx", all_files, None) == [
        "src/auth/AuthProvider.test.tsx"
    ]
    assert find_test_files("src/components/Address/Address.tsx", all_files, None) == [
        "src/components/Address/Address.test.tsx"
    ]
    assert find_test_files(
        "src/components/CoverageOption/index.tsx", all_files, None
    ) == ["src/components/CoverageOption/index.test.tsx"]
    assert find_test_files("src/apolloClient.ts", all_files, None) == [
        "src/apolloClient.test.ts"
    ]


def test_real_foxcom_forms_backend():
    # foxcom-forms-backend: 611 files. Colocated + mirror test/testing/ dirs.
    all_files = _load_fixture("foxcom-forms-backend")
    assert len(all_files) > 500
    assert find_test_files(
        "src/context/amTrust/classCodes/common.ts", all_files, None
    ) == ["src/context/amTrust/classCodes/common.test.ts"]
    # createQuoteProposal has both colocated and mirror test
    assert find_test_files(
        "src/context/amTrust/createQuoteProposal.ts", all_files, None
    ) == [
        "src/context/amTrust/createQuoteProposal.test.ts",
        "test/testing/amtrust/createQuoteProposal.test.ts",
    ]


def test_real_foxcom_payment_backend():
    # foxcom-payment-backend: 811 files. Colocated + mirror test/ and test/testing/ dirs.
    all_files = _load_fixture("foxcom-payment-backend")
    assert len(all_files) > 700
    assert find_test_files("src/context/getSecrets.ts", all_files, None) == [
        "src/context/getSecrets.test.ts"
    ]
    assert find_test_files("src/createGenericServer.ts", all_files, None) == [
        "src/createGenericServer.test.ts"
    ]
    # policyDocumentClient has mirror test + mirror testing (case-insensitive match)
    assert find_test_files("src/client/policyDocumentClient.ts", all_files, None) == [
        "test/client/policyDocumentClient.test.ts",
        "test/testing/client/PolicyDocumentClient.spec.ts",
    ]


def test_real_foxcom_payment_frontend():
    # foxcom-payment-frontend: 213 files. Both colocated src/ and mirror test/ dirs.
    all_files = _load_fixture("foxcom-payment-frontend")
    assert len(all_files) > 200
    assert find_test_files("src/utils/calTotalPayable.ts", all_files, None) == [
        "src/utils/calTotalPayable.test.ts"
    ]
    assert find_test_files("src/utils/getDelay.ts", all_files, None) == [
        "src/utils/getDelay.test.ts"
    ]
    # AuthProvider has colocated and mirror test (__mocks__/AuthProvider.tsx excluded)
    assert find_test_files("src/auth/AuthProvider.tsx", all_files, None) == [
        "src/auth/AuthProvider.test.tsx",
        "test/auth/AuthProvider.test.tsx",
    ]


def test_real_foxden_admin_portal():
    # foxden-admin-portal: 205 files. Both colocated src/ and mirror test/ dirs.
    all_files = _load_fixture("foxden-admin-portal")
    assert len(all_files) > 200
    assert find_test_files("src/components/Header/index.tsx", all_files, None) == [
        "src/components/Header/index.test.tsx"
    ]
    assert find_test_files(
        "src/components/Sidebar/SidebarDropdownItem.tsx", all_files, None
    ) == ["src/components/Sidebar/SidebarDropdownItem.test.tsx"]
    # App.tsx has only mirror test (no colocated)
    assert find_test_files("src/App.tsx", all_files, None) == ["test/App.test.tsx"]


def test_real_foxden_admin_portal_backend():
    # foxden-admin-portal-backend: 460 files. Colocated .test.ts pattern.
    all_files = _load_fixture("foxden-admin-portal-backend")
    assert len(all_files) > 400
    assert find_test_files("src/context/getSecrets.ts", all_files, None) == [
        "src/context/getSecrets.test.ts"
    ]
    assert find_test_files("src/context/index.ts", all_files, None) == [
        "src/context/index.test.ts"
    ]
    assert find_test_files("src/create-express-server.ts", all_files, None) == [
        "src/create-express-server.test.ts"
    ]


def test_real_foxden_auth_service():
    # foxden-auth-service: 114 files. Mirror test/spec/ for src/.
    all_files = _load_fixture("foxden-auth-service")
    assert len(all_files) > 100
    assert find_test_files("src/config.ts", all_files, None) == [
        "test/spec/config.spec.ts"
    ]
    assert find_test_files("src/auth-service-secrets.ts", all_files, None) == [
        "test/spec/auth-service-secrets.spec.ts"
    ]
    assert find_test_files("src/create-dependencies.ts", all_files, None) == [
        "test/spec/create-dependencies.spec.ts"
    ]


def test_real_foxden_billing():
    # foxden-billing: 374 files. Both colocated and mirror testing/ dir.
    all_files = _load_fixture("foxden-billing")
    assert len(all_files) > 300
    assert find_test_files(
        "src/models/graphql/scalars/CanadaTimeZoneResolver.ts", all_files, None
    ) == [
        "src/models/graphql/scalars/CanadaTimeZoneResolver.test.ts",
        "testing/models/graphql/scalars/CanadaTimeZoneResolver.test.ts",
    ]
    assert find_test_files(
        "src/models/graphql/scalars/utils/checkISODate.ts", all_files, None
    ) == [
        "src/models/graphql/scalars/utils/checkISODate.test.ts",
        "testing/models/graphql/scalars/utils/checkISODate.test.ts",
    ]


def test_real_foxden_policy_document_backend():
    # foxden-policy-document-backend: 915 files. Colocated .test.ts pattern.
    all_files = _load_fixture("foxden-policy-document-backend")
    assert len(all_files) > 900
    assert find_test_files("src/models/graphql/generatePDF.ts", all_files, None) == [
        "src/models/graphql/generatePDF.test.ts"
    ]
    assert find_test_files(
        "src/resolvers/generateAndSendPolicyDocumentResolver.ts", all_files, None
    ) == ["src/resolvers/generateAndSendPolicyDocumentResolver.test.ts"]


def test_real_foxden_rating_quoting_backend():
    # foxden-rating-quoting-backend: 1659 files. Both colocated and mirror test/ dir.
    all_files = _load_fixture("foxden-rating-quoting-backend")
    assert len(all_files) > 1600
    assert find_test_files("src/context/amTrust/adapter.ts", all_files, None) == [
        "src/context/amTrust/adapter.test.ts"
    ]
    # CanadaProvinceResolver has only mirror test (no colocated)
    assert find_test_files(
        "src/models/graphql/scalars/CanadaProvinceResolver.ts", all_files, None
    ) == ["test/models/graphql/scalars/CanadaProvinceResolver.test.ts"]


def test_real_foxden_shared_lib():
    # foxden-shared-lib: 295 files. Colocated .spec.ts pattern.
    all_files = _load_fixture("foxden-shared-lib")
    assert len(all_files) > 200
    assert find_test_files(
        "src/authorization/authorizers/agencyAuthorizationHandler.handler.ts",
        all_files,
        None,
    ) == ["src/authorization/authorizers/agencyAuthorizationHandler.handler.spec.ts"]


def test_real_foxden_tools():
    # foxden-tools: 189 files. Mirror test/ for src/.
    all_files = _load_fixture("foxden-tools")
    assert len(all_files) > 180
    assert find_test_files(
        "src/UpdateUserAndAgencyList/createAuth0User.ts", all_files, None
    ) == ["test/UpdateUserAndAgencyList/createAuth0User.spec.ts"]
    assert find_test_files(
        "src/UpdateUserAndAgencyList/updateAgencyList.ts", all_files, None
    ) == ["test/UpdateUserAndAgencyList/updateAgencyList.spec.ts"]


def test_real_foxden_version_controller():
    # foxden-version-controller: 83 files. Mirror test/spec/ for src/.
    all_files = _load_fixture("foxden-version-controller")
    assert len(all_files) > 80
    assert find_test_files("src/config.ts", all_files, None) == [
        "test/spec/config.spec.ts"
    ]
    assert find_test_files("src/create-express-server.ts", all_files, None) == [
        "test/spec/create-express-server.spec.ts"
    ]
    assert find_test_files(
        "src/resolvers/getNewBusinessVersionResolver.ts", all_files, None
    ) == ["test/spec/resolvers/getNewBusinessVersionResolver.spec.ts"]
    assert find_test_files(
        "src/services/getNewBusinessVersion.ts", all_files, None
    ) == ["test/spec/services/getNewBusinessVersion.spec.ts"]


def test_real_foxden_version_controller_client():
    # foxden-version-controller-client: 20 files. Colocated .test.ts pattern.
    all_files = _load_fixture("foxden-version-controller-client")
    assert len(all_files) >= 20
    assert find_test_files("src/index.ts", all_files, None) == ["src/index.test.ts"]


def test_real_gitauto():
    # gitauto: 897 files. Python test_ prefix colocated pattern.
    all_files = _load_fixture("gitauto")
    assert len(all_files) > 800
    assert find_test_files("utils/files/find_test_files.py", all_files, None) == [
        "utils/files/test_find_test_files.py"
    ]
    assert find_test_files("services/webhook/schedule_handler.py", all_files, None) == [
        "services/webhook/test_schedule_handler.py"
    ]
    assert find_test_files("utils/pr_templates/schedule.py", all_files, None) == [
        "utils/pr_templates/test_schedule.py"
    ]


def test_real_website():
    # website: 1022 files. Next.js colocated .test.ts pattern.
    all_files = _load_fixture("website")
    assert len(all_files) > 1000
    # disable-schedules has both .integration.test.ts and .test.ts
    assert find_test_files("app/actions/aws/disable-schedules.ts", all_files, None) == [
        "app/actions/aws/disable-schedules.integration.test.ts",
        "app/actions/aws/disable-schedules.test.ts",
    ]
    assert find_test_files(
        "app/actions/github/get-default-branch.ts", all_files, None
    ) == ["app/actions/github/get-default-branch.test.ts"]
    # get-credit-balance has both .integration.test.ts and .test.ts
    assert find_test_files(
        "app/actions/supabase/owners/get-credit-balance.ts", all_files, None
    ) == [
        "app/actions/supabase/owners/get-credit-balance.integration.test.ts",
        "app/actions/supabase/owners/get-credit-balance.test.ts",
    ]


def test_real_spiderplus_phpunit_unit():
    # SPIDERPLUS-web: 13608 files. PHPUnit Unit tests with plural tolerance.
    # core/tests/Unit/Service/ mirrors core/app/Services/ (Service vs Services).
    # core/tests/Unit/Model/ mirrors core/app/Models/ (Model vs Models).
    # test_dir_prefixes is always passed for the whole repo, not just plain PHP files.
    all_files = _load_fixture("spiderplus-web")
    assert len(all_files) > 13000
    prefixes = ["tests/php/unit", "tests/js/unit"]
    assert find_test_files(
        "core/app/Services/SafetypatService.php", all_files, prefixes
    ) == ["core/tests/Unit/Service/SafetypatServiceTest.php"]
    assert find_test_files(
        "core/app/Services/OrganizationService.php", all_files, prefixes
    ) == ["core/tests/Unit/Service/OrganizationServiceTest.php"]
    assert find_test_files(
        "core/app/Models/SafetypatAnnotation.php", all_files, prefixes
    ) == ["core/tests/Unit/Model/SafetypatAnnotationTest.php"]


def test_real_spiderplus_plain_php():
    # SPIDERPLUS-web: Plain PHP tests under tests/php/unit/.
    # test_dir_prefixes from DB: ["tests/php/unit", "tests/js/unit"]
    # tests/php/unit/core/app/... mirrors core/app/...
    # tests/php/unit/bin/... mirrors bin/...
    # tests/php/unit/php/... mirrors php/...
    all_files = _load_fixture("spiderplus-web")
    prefixes = ["tests/php/unit", "tests/js/unit"]
    assert find_test_files(
        "core/app/Http/Controllers/Api/Sys/CacheController.php",
        all_files,
        test_dir_prefixes=prefixes,
    ) == ["tests/php/unit/core/app/Http/Controllers/Api/Sys/CacheControllerTest.php"]
    assert find_test_files(
        "core/app/Helpers/validatorRule.php",
        all_files,
        test_dir_prefixes=prefixes,
    ) == ["tests/php/unit/core/app/Helpers/validatorRuleTest.php"]
    assert find_test_files(
        "bin/file_migration/BatchMoveCadToS3Func.php",
        all_files,
        test_dir_prefixes=prefixes,
    ) == ["tests/php/unit/bin/file_migration/BatchMoveCadToS3FuncTest.php"]
    assert find_test_files(
        "php/DboAdapter.php",
        all_files,
        test_dir_prefixes=prefixes,
    ) == ["tests/php/unit/php/DboAdapterTest.php"]


def test_real_spiderplus_phpunit_feature():
    # SPIDERPLUS-web: PHPUnit Feature tests (standard Laravel convention).
    # core/tests/Feature/Api/V1/Direct/ mirrors core/app/Http/Controllers/Api/V1/Direct/
    # via suffix matching (Api/V1/Direct suffix shared, prefix core shared).
    # test_dir_prefixes is always passed for the whole repo, not just plain PHP files.
    all_files = _load_fixture("spiderplus-web")
    prefixes = ["tests/php/unit", "tests/js/unit"]
    assert find_test_files(
        "core/app/Http/Controllers/Api/V1/Direct/DirectController.php",
        all_files,
        prefixes,
    ) == ["core/tests/Feature/Api/V1/Direct/DirectControllerTest.php"]
    assert find_test_files(
        "core/app/Http/Controllers/Api/V1/Organization/OrganizationController.php",
        all_files,
        prefixes,
    ) == ["core/tests/Feature/Api/V1/Organization/OrganizationControllerTest.php"]
    assert find_test_files(
        "core/app/Console/Commands/GenerateReport.php", all_files, prefixes
    ) == ["core/tests/Feature/Console/Commands/GenerateReportTest.php"]


def test_real_spiderplus_js_unit():
    # SPIDERPLUS-web: JS unit tests under tests/js/unit/.
    # test_dir_prefixes from DB: ["tests/php/unit", "tests/js/unit"]
    # tests/js/unit/CsvUploadArea.test.js tests web/js/annotation/CsvUploadArea.js
    # tests/js/unit/ThumbnailBookFactory.test.js tests web/js/blueprints/ThumbnailBookFactory.js
    all_files = _load_fixture("spiderplus-web")
    prefixes = ["tests/php/unit", "tests/js/unit"]
    assert find_test_files(
        "web/js/annotation/CsvUploadArea.js", all_files, prefixes
    ) == ["tests/js/unit/CsvUploadArea.test.js"]
    assert find_test_files(
        "web/js/blueprints/ThumbnailBookFactory.js", all_files, prefixes
    ) == ["tests/js/unit/ThumbnailBookFactory.test.js"]
    assert find_test_files(
        "web/js/blueprints/ThumbnailDrawFactory.js", all_files, prefixes
    ) == ["tests/js/unit/ThumbnailDrawFactory.test.js"]
