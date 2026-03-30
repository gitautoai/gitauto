from utils.files.prioritize_test_files import prioritize_test_files


# ---- Real repo: Foxquilt foxcom-forms ----
# All paths verified by running find_test_files against ../Foxquilt/foxcom-forms clone


def test_foxquilt_authprovider_ranks_colocated_first():
    """foxcom-forms: find_test_files('src/auth/AuthProvider.tsx') returns 5 hits.
    Colocated AuthProvider.test.tsx should rank first."""
    impl = "src/auth/AuthProvider.tsx"
    tests = [
        "src/auth/AuthProvider.test.tsx",
        "src/pages/Quote/Quote.master.test.tsx",
        "src/pages/Quote/Quote.test.tsx",
        "src/pages/Quote/index.test.tsx",
        "src/pages/Quote/components/BuyNowButton/index.test.tsx",
    ]
    result = prioritize_test_files(tests, impl)
    # Colocated name match: AuthProvider.test.tsx has stem match + same dir
    assert result[0] == "src/auth/AuthProvider.test.tsx"
    assert len(result) == 5


def test_foxquilt_index_tsx_ranks_colocated_first():
    """foxcom-forms: find_test_files('src/pages/Quote/index.tsx') returns 31 hits.
    This is the original problem case — generic stem 'index' matches many files."""
    impl = "src/pages/Quote/index.tsx"
    tests = [
        "cypress/integration/basic/e2eUnderwritingToQuoteBasic.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_MoreThan20Employee.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_OutSideCanadaAndUS.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_RevenueMoreThan15M.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteComplete.spec.ts",
        "cypress/integration/basic/e2eUnderwritngtoQuoteDiffProfessions.spec.ts",
        "cypress/integration/full/e2eUnderwritingToQuoteBroker_AllProfessions.spec.ts",
        "src/components/CoverageOption/index.test.tsx",
        "src/components/Customer/index.test.tsx",
        "src/components/DatePicker/index.test.tsx",
        "src/components/Header/index.test.tsx",
        "src/components/Input/index.test.tsx",
        "src/components/QuotePageSelectInput/index.test.tsx",
        "src/components/SearchSelect/index.test.tsx",
        "src/components/SelectInput/index.test.tsx",
        "src/components/SliderBar/index.test.tsx",
        "src/components/ToggleButton/index.test.tsx",
        "src/index.test.tsx",
        "src/pages/BrokerComplete/index.test.tsx",
        "src/pages/Commercial/CommercialSurvey/index.test.tsx",
        "src/pages/CommercialWithApplicationId/CommercialSurveyWithApplicationId/index.test.tsx",
        "src/pages/Quote/components/BuyNowButton/index.test.tsx",
        "src/pages/Quote/components/Coverages/index.test.tsx",
        "src/pages/Quote/components/CustomerAgreement/CustomerAgreement.test.tsx",
        "src/pages/Quote/components/Premium/index.test.tsx",
        "src/pages/Quote/components/QuoteLinkPopup/index.test.tsx",
        "src/pages/Quote/components/Summary/index.test.tsx",
        "src/pages/Quote/index.test.tsx",
        "src/utils/questionTracking.test.ts",
        "test/utils/getVersionedURL.test.ts",
        "test/utils/questionTracking.test.ts",
    ]
    result = prioritize_test_files(tests, impl)
    assert result == [
        # Same dir + name match (score 148)
        "src/pages/Quote/index.test.tsx",
        # Name match + 3 shared components "src/pages/Quote/" (score 126)
        "src/pages/Quote/components/BuyNowButton/index.test.tsx",
        "src/pages/Quote/components/Coverages/index.test.tsx",
        "src/pages/Quote/components/Premium/index.test.tsx",
        "src/pages/Quote/components/QuoteLinkPopup/index.test.tsx",
        "src/pages/Quote/components/Summary/index.test.tsx",
        # Name match + 2 shared components "src/pages/" (score 116)
        "src/pages/BrokerComplete/index.test.tsx",
        "src/pages/Commercial/CommercialSurvey/index.test.tsx",
        "src/pages/CommercialWithApplicationId/CommercialSurveyWithApplicationId/index.test.tsx",
        # Name match + 1 shared component "src/" (score 106)
        "src/index.test.tsx",
        "src/components/CoverageOption/index.test.tsx",
        "src/components/Customer/index.test.tsx",
        "src/components/DatePicker/index.test.tsx",
        "src/components/Header/index.test.tsx",
        "src/components/Input/index.test.tsx",
        "src/components/QuotePageSelectInput/index.test.tsx",
        "src/components/SearchSelect/index.test.tsx",
        "src/components/SelectInput/index.test.tsx",
        "src/components/SliderBar/index.test.tsx",
        "src/components/ToggleButton/index.test.tsx",
        # No name match, 3 shared components "src/pages/Quote/" (score 26)
        "src/pages/Quote/components/CustomerAgreement/CustomerAgreement.test.tsx",
        # No name match, 1 shared component "src/" (score 4)
        "src/utils/questionTracking.test.ts",
        # No name match, no shared components (score -6)
        "test/utils/getVersionedURL.test.ts",
        "test/utils/questionTracking.test.ts",
        # Cypress: no name match, no shared components (score -10 to -11)
        "cypress/integration/basic/e2eUnderwritingToQuoteBasic.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_MoreThan20Employee.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_OutSideCanadaAndUS.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_RevenueMoreThan15M.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteComplete.spec.ts",
        "cypress/integration/basic/e2eUnderwritngtoQuoteDiffProfessions.spec.ts",
        "cypress/integration/full/e2eUnderwritingToQuoteBroker_AllProfessions.spec.ts",
    ]


def test_foxquilt_quote_tsx_ranks_colocated_first():
    """foxcom-forms: find_test_files('src/pages/Quote/Quote.tsx') returns 34 hits.
    Non-generic stem 'Quote' — colocated tests should rank above cypress and distant."""
    impl = "src/pages/Quote/Quote.tsx"
    tests = [
        "cypress/integration/basic/e2eUnderwritingToQuoteBasic.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_MoreThan20Employee.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_OutSideCanadaAndUS.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteBroker_RevenueMoreThan15M.spec.ts",
        "cypress/integration/basic/e2eUnderwritingToQuoteComplete.spec.ts",
        "cypress/integration/basic/e2eUnderwritngtoQuoteDiffProfessions.spec.ts",
        "cypress/integration/full/e2eUnderwritingToQuoteBroker_AllProfessions.spec.ts",
        "src/App.test.tsx",
        "src/auth/AuthProvider.test.tsx",
        "src/backend-client/createRatingQuotingBackend.test.ts",
        "src/backend-client/paymentBackend.test.ts",
        "src/backend-client/ratingQuotingBackend.test.ts",
        "src/components/Header/index.test.tsx",
        "src/components/QuotePageSelectInput/SelectInput.stories.tsx",
        "src/components/QuotePageSelectInput/SelectInput.test.tsx",
        "src/components/QuotePageSelectInput/index.test.tsx",
        "src/components/SearchSelect/SearchSelect.test.tsx",
        "src/pages/CommercialWithApplicationId/CommercialSurveyWithApplicationId/index.test.tsx",
        "src/pages/Quote/Quote.master.test.tsx",
        "src/pages/Quote/Quote.test.tsx",
        "src/pages/Quote/components/BuyNowButton/index.test.tsx",
        "src/pages/Quote/components/Coverages/Coverage.test.tsx",
        "src/pages/Quote/components/Coverages/CoveragesDetails.test.ts",
        "src/pages/Quote/components/Coverages/index.test.tsx",
        "src/pages/Quote/components/CustomerAgreement/CustomerAgreement.test.tsx",
        "src/pages/Quote/components/FeinInputBox/Popup.test.tsx",
        "src/pages/Quote/components/Premium/index.test.tsx",
        "src/pages/Quote/components/QuoteLinkPopup/index.test.tsx",
        "src/pages/Quote/components/ReturnToQuotePopup/ReturnToQuotePopup.test.tsx",
        "src/pages/Quote/components/Summary/SummaryCoverage.test.tsx",
        "src/pages/Quote/components/Summary/index.test.tsx",
        "src/pages/Quote/index.test.tsx",
        "src/pages/QuoteExpired/QuoteExpired.test.tsx",
        "test/utils/getVersionedUrlFromPaymentFrontend.test.ts",
    ]
    result = prioritize_test_files(tests, impl)
    assert len(result) == 34
    # Colocated tests with 'Quote' in name rank first
    assert result[0] == "src/pages/Quote/Quote.master.test.tsx"
    assert result[1] == "src/pages/Quote/Quote.test.tsx"
    # QuoteExpired also has 'Quote' in stem — name match but different dir
    assert "src/pages/QuoteExpired/QuoteExpired.test.tsx" in result[:5]
