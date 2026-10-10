-- Synthetic banking system-of-record + case corpus.
-- Everything is fictional. Money is stored in minor units (pence/cents).
-- Timestamps are ISO-8601 UTC strings ("2025-07-19 09:00:00").

PRAGMA foreign_keys = ON;

------------------------------------------------------------------------------
-- Reference data
------------------------------------------------------------------------------

CREATE TABLE banks (
    bank_id         TEXT PRIMARY KEY,          -- 'HV'
    name            TEXT NOT NULL,             -- 'Harrow & Vale Bank plc'
    short_name      TEXT NOT NULL,             -- 'H&V'
    sort_code_prefix TEXT NOT NULL,
    is_home_bank    INTEGER NOT NULL DEFAULT 0 -- 1 = the bank whose agent handles cases
);

-- Systems an agent can query or instruct (the "tools" of the bank).
CREATE TABLE systems (
    system_id       TEXT PRIMARY KEY,          -- 'transfer_journal'
    display_name    TEXT NOT NULL,             -- 'H&V transfer journal'
    kind            TEXT NOT NULL,             -- record | process | team | channel
    description     TEXT NOT NULL,
    read_only       INTEGER NOT NULL DEFAULT 1
);

------------------------------------------------------------------------------
-- Parties
------------------------------------------------------------------------------

CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,          -- 'CUS-000123'
    bank_id         TEXT NOT NULL REFERENCES banks(bank_id),
    full_name       TEXT NOT NULL,
    preferred_name  TEXT,
    title           TEXT,
    pronoun_hint    TEXT,                      -- as stated by the customer, else NULL
    date_of_birth   TEXT,
    address_line    TEXT NOT NULL,
    town            TEXT NOT NULL,
    postcode        TEXT NOT NULL,
    correspondence_address TEXT,               -- if different
    mobile_masked   TEXT,                      -- '07*** ***482'
    email_masked    TEXT,
    language        TEXT NOT NULL DEFAULT 'en',
    customer_since  TEXT,
    status          TEXT NOT NULL DEFAULT 'active', -- active | deceased | closed | restricted
    date_of_death   TEXT,
    kyc_status      TEXT NOT NULL DEFAULT 'verified' -- verified | refresh_due | incomplete
);

CREATE TABLE businesses (
    business_id     TEXT PRIMARY KEY,          -- 'BUS-000045'
    bank_id         TEXT NOT NULL REFERENCES banks(bank_id),
    legal_name      TEXT NOT NULL,
    trading_name    TEXT,
    company_number  TEXT,
    sector          TEXT,
    dual_authorisation INTEGER NOT NULL DEFAULT 0,
    daily_payment_limit_minor INTEGER,
    status          TEXT NOT NULL DEFAULT 'active'
);

-- People who act for a business on online/business banking.
CREATE TABLE business_users (
    user_id         TEXT PRIMARY KEY,          -- 'BU-000201'
    business_id     TEXT NOT NULL REFERENCES businesses(business_id),
    full_name       TEXT NOT NULL,
    job_title       TEXT,
    status          TEXT NOT NULL,             -- active | pending_approval | revoked | suspended
    created_at      TEXT,
    revoked_at      TEXT
);

CREATE TABLE business_user_roles (
    user_id         TEXT NOT NULL REFERENCES business_users(user_id),
    role            TEXT NOT NULL,             -- administrator | uploader | approver | signatory | viewer | report_viewer | accountant
    granted_at      TEXT,
    revoked_at      TEXT,
    PRIMARY KEY (user_id, role)
);

-- Third parties with some recognised (or claimed) relationship to a customer.
CREATE TABLE third_party_authorities (
    authority_id    TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id),
    person_name     TEXT NOT NULL,
    relationship    TEXT NOT NULL,             -- attorney | deputy | executor | additional_cardholder | trusted_contact | claimed_only
    instrument      TEXT,                      -- 'Lasting power of attorney (property & financial)' etc.
    status          TEXT NOT NULL,             -- registered | pending_verification | rejected | none_on_record | revoked
    registered_at   TEXT,
    scope           TEXT
);

-- Support / vulnerability notes. Sensitive: disclosure rules apply.
CREATE TABLE vulnerability_notes (
    note_id         TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers(customer_id),
    category        TEXT NOT NULL,             -- economic_abuse | bereavement | health | capability | financial_difficulty | gambling | language | literacy | coercion_suspected | scam_victim
    recorded_at     TEXT NOT NULL,
    consent_given   INTEGER NOT NULL DEFAULT 0,
    contact_preference TEXT,                   -- e.g. 'secure chat only; no post; no calls to home number'
    detail          TEXT
);

------------------------------------------------------------------------------
-- Accounts and money movement
------------------------------------------------------------------------------

CREATE TABLE accounts (
    account_id      TEXT PRIMARY KEY,          -- 'ACC-000123'
    bank_id         TEXT NOT NULL REFERENCES banks(bank_id),
    product         TEXT NOT NULL,             -- current | savings | joint_current | business_current | fixed_bond | isa
    sort_code       TEXT NOT NULL,
    account_number_masked TEXT NOT NULL,       -- '****4821'
    nickname        TEXT,
    currency        TEXT NOT NULL DEFAULT 'GBP',
    status          TEXT NOT NULL,             -- open | restricted | closing | closed | dormant | frozen_deceased
    opened_at       TEXT,
    closed_at       TEXT,
    balance_minor   INTEGER,
    available_minor INTEGER,
    overdraft_limit_minor INTEGER DEFAULT 0,
    interest_rate_pct REAL,
    restriction_reason TEXT                    -- internal; disclosure rules apply
);

-- Holders: a customer or a business (exactly one non-null).
CREATE TABLE account_holders (
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    holder_role     TEXT NOT NULL,             -- sole | joint | business
    CHECK ((customer_id IS NULL) <> (business_id IS NULL))
);

CREATE TABLE payees (
    payee_id        TEXT PRIMARY KEY,
    owner_account_id TEXT NOT NULL REFERENCES accounts(account_id),
    name            TEXT NOT NULL,
    bank_name       TEXT,
    sort_code       TEXT,
    account_number_masked TEXT,
    iban_masked     TEXT,
    country         TEXT DEFAULT 'GB',
    added_at        TEXT,
    cop_result      TEXT                       -- match | close_match | no_match | not_checked | unavailable
);

-- Ledger lines visible in account activity.
CREATE TABLE transactions (
    txn_id          TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    posted_at       TEXT,                      -- NULL if pending
    value_date      TEXT,
    state           TEXT NOT NULL,             -- pending | posted | reversed
    kind            TEXT NOT NULL,             -- card_purchase | transfer_out | transfer_in | direct_debit | standing_order | fee | refund | interest | atm | cheque | chargeback_credit
    description     TEXT NOT NULL,
    amount_minor    INTEGER NOT NULL,          -- negative = debit
    currency        TEXT NOT NULL DEFAULT 'GBP',
    counterparty    TEXT,
    reference       TEXT,
    linked_id       TEXT                       -- transfer_id / card_auth_id / mandate collection etc.
);

-- Outgoing one-off transfers (and their lifecycle).
CREATE TABLE transfers (
    transfer_id     TEXT PRIMARY KEY,          -- 'TRF-000123'
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    payee_id        TEXT REFERENCES payees(payee_id),
    scheme          TEXT NOT NULL,             -- faster_payments | chaps | bacs | swift | sepa | internal
    amount_minor    INTEGER NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'GBP',
    fx_rate         REAL,
    amount_sent_minor INTEGER,                 -- in destination currency, if FX
    dest_currency   TEXT,
    reference       TEXT,
    purpose         TEXT,
    created_at      TEXT NOT NULL,
    created_via     TEXT,                      -- app | online | branch | phone | business_portal
    status          TEXT NOT NULL,             -- draft | awaiting_authorisation | authorised | held_for_review | declined | sent | returned | recalled | cancelled
    status_at       TEXT,
    decline_reason  TEXT,                      -- internal reason code text; disclosure rules apply
    customer_facing_reason TEXT,               -- what may be told to the customer
    uetr            TEXT,
    debit_txn_id    TEXT,
    recipient_credit_confirmed INTEGER,        -- NULL = unknown (normal), 1/0 only if a confirmation exists
    notes           TEXT
);

-- Recall / misdirected-payment / APP-scam reimbursement requests.
CREATE TABLE payment_recalls (
    recall_id       TEXT PRIMARY KEY,
    transfer_id     TEXT REFERENCES transfers(transfer_id),  -- NULL when recalling a batch line
    batch_id        TEXT,
    line_no         INTEGER,
    reason          TEXT NOT NULL,             -- wrong_recipient | duplicate | app_scam | wrong_amount
    raised_at       TEXT NOT NULL,
    status          TEXT NOT NULL,             -- registered | sent_to_receiving_bank | funds_returned | partially_returned | unsuccessful | under_review
    status_at       TEXT,
    outcome_note    TEXT
);

CREATE TABLE incoming_payments (
    incoming_id     TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    payer_name      TEXT,
    scheme          TEXT,
    amount_minor    INTEGER NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'GBP',
    reference       TEXT,
    received_at     TEXT,
    status          TEXT NOT NULL,             -- credited | held | returned | not_found
    hold_reason     TEXT,                      -- internal; disclosure rules apply
    credit_txn_id   TEXT
);

CREATE TABLE standing_orders (
    so_id           TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    payee_id        TEXT REFERENCES payees(payee_id),
    amount_minor    INTEGER NOT NULL,
    frequency       TEXT NOT NULL,             -- weekly | monthly | quarterly | annually
    next_run_date   TEXT,
    final_run_date  TEXT,
    reference       TEXT,
    status          TEXT NOT NULL,             -- active | cancelled | amendment_pending | suspended
    created_at      TEXT,
    updated_at      TEXT
);

CREATE TABLE standing_order_runs (
    run_id          TEXT PRIMARY KEY,
    so_id           TEXT NOT NULL REFERENCES standing_orders(so_id),
    scheduled_date  TEXT NOT NULL,
    executed        INTEGER NOT NULL,
    result          TEXT NOT NULL,             -- paid | not_executed | skipped_holiday | pending
    reason          TEXT,
    txn_id          TEXT
);

CREATE TABLE dd_mandates (
    mandate_id      TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    originator_name TEXT NOT NULL,
    service_user_number TEXT,
    reference       TEXT,
    status          TEXT NOT NULL,             -- active | cancelled | dormant | pending_setup
    set_up_at       TEXT,
    cancelled_at    TEXT,
    last_collection_at TEXT
);

CREATE TABLE dd_collections (
    collection_id   TEXT PRIMARY KEY,
    mandate_id      TEXT NOT NULL REFERENCES dd_mandates(mandate_id),
    due_date        TEXT NOT NULL,
    amount_minor    INTEGER NOT NULL,
    stage           TEXT NOT NULL,             -- advance_notice | in_processing | collected | unpaid | returned
    advance_notice_amount_minor INTEGER,       -- what the originator told the customer, if known
    txn_id          TEXT
);

-- Direct Debit Guarantee indemnity claims.
CREATE TABLE dd_indemnity_claims (
    claim_id        TEXT PRIMARY KEY,
    collection_id   TEXT NOT NULL REFERENCES dd_collections(collection_id),
    raised_at       TEXT NOT NULL,
    status          TEXT NOT NULL,             -- registered | refunded | challenged_by_originator | rejected
    refund_txn_id   TEXT
);

------------------------------------------------------------------------------
-- Cards
------------------------------------------------------------------------------

CREATE TABLE cards (
    card_id         TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    holder_customer_id TEXT REFERENCES customers(customer_id),
    pan_last4       TEXT NOT NULL,
    card_type       TEXT NOT NULL,             -- debit | credit | business_debit
    status          TEXT NOT NULL,             -- active | frozen_by_customer | blocked_lost | blocked_stolen | blocked_fraud | restricted | expired | cancelled | replacement_ordered | not_activated
    status_at       TEXT,
    expiry          TEXT,
    contactless     INTEGER DEFAULT 1,
    gambling_block  INTEGER DEFAULT 0,
    restriction_reason TEXT                    -- internal; disclosure rules apply
);

CREATE TABLE card_dispatches (
    dispatch_id     TEXT PRIMARY KEY,
    card_id         TEXT NOT NULL REFERENCES cards(card_id),
    reason          TEXT NOT NULL,             -- replacement_damaged | replacement_lost | renewal | new_account | pin_reminder
    ordered_at      TEXT NOT NULL,
    dispatched_at   TEXT,
    delivery_method TEXT,                      -- standard_post | tracked | branch_collection
    address_used    TEXT,                      -- masked/partial
    returned_at     TEXT,
    status          TEXT NOT NULL              -- ordered | dispatched | returned_undelivered | cancelled
);

CREATE TABLE card_authorisations (
    auth_id         TEXT PRIMARY KEY,
    card_id         TEXT NOT NULL REFERENCES cards(card_id),
    attempted_at    TEXT NOT NULL,
    merchant        TEXT NOT NULL,
    merchant_country TEXT DEFAULT 'GB',
    amount_minor    INTEGER NOT NULL,
    currency        TEXT DEFAULT 'GBP',
    channel         TEXT,                      -- chip_pin | contactless | online | atm | wallet
    result          TEXT NOT NULL,             -- approved | declined
    decline_code    TEXT,                      -- internal code; disclosure rules apply
    customer_facing_reason TEXT,
    txn_id          TEXT
);

CREATE TABLE card_disputes (
    dispute_id      TEXT PRIMARY KEY,
    card_id         TEXT NOT NULL REFERENCES cards(card_id),
    txn_id          TEXT,
    category        TEXT NOT NULL,             -- unrecognised | goods_not_received | duplicate | cancelled_subscription | atm_not_dispensed
    raised_at       TEXT NOT NULL,
    status          TEXT NOT NULL,             -- registered | temporary_credit | chargeback_raised | resolved_refund | resolved_no_refund
    reference       TEXT
);

------------------------------------------------------------------------------
-- Digital access & security
------------------------------------------------------------------------------

CREATE TABLE devices (
    device_id       TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(customer_id),
    business_user_id TEXT REFERENCES business_users(user_id),
    label           TEXT NOT NULL,             -- 'Tablet (registration started 13 Sep 2025)'
    status          TEXT NOT NULL,             -- active | awaiting_confirmation | removed | blocked
    registered_at   TEXT,
    last_seen_at    TEXT
);

CREATE TABLE sign_in_events (
    event_id        TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(customer_id),
    business_user_id TEXT REFERENCES business_users(user_id),
    at              TEXT NOT NULL,
    device_label    TEXT,
    method          TEXT,                      -- app_biometric | passcode | one_time_code | card_reader
    result          TEXT NOT NULL,             -- success | failed | locked
    approx_location TEXT
);

CREATE TABLE access_status (
    customer_id     TEXT PRIMARY KEY REFERENCES customers(customer_id),
    online_status   TEXT NOT NULL,             -- active | locked_failed_attempts | suspended_security | restored
    status_at       TEXT,
    note            TEXT
);

CREATE TABLE profile_change_requests (
    request_id      TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    field           TEXT NOT NULL,             -- mobile_number | correspondence_address | name | email | permitted_sign_in
    requested_via   TEXT NOT NULL,             -- channel the request came in by
    old_value_masked TEXT,
    new_value_masked TEXT,
    status          TEXT NOT NULL,             -- received_unverified | awaiting_customer_confirmation | awaiting_evidence | completed | rejected | cancelled
    status_at       TEXT,
    note            TEXT
);

-- Fraud/scam reports and security events.
CREATE TABLE security_reports (
    report_id       TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    kind            TEXT NOT NULL,             -- unauthorised_mandate | smishing | vishing | impersonation | account_takeover | app_scam | invoice_redirection | sim_swap | phishing_email
    reported_at     TEXT NOT NULL,
    bank_sent_message INTEGER,                 -- 1 bank sent it, 0 bank did not, NULL unknown
    credentials_shared INTEGER,                -- per customer, NULL unknown
    status          TEXT NOT NULL,             -- received | under_review | closed
    reference       TEXT,
    summary         TEXT
);

------------------------------------------------------------------------------
-- Fees, documents, statements
------------------------------------------------------------------------------

CREATE TABLE fees (
    fee_id          TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES accounts(account_id),
    fee_type        TEXT NOT NULL,             -- monthly_account | unarranged_overdraft | international_payment | chaps | replacement_card_express | returned_item | paper_statement
    amount_minor    INTEGER NOT NULL,
    charged_at      TEXT NOT NULL,
    tariff_ref      TEXT,
    basis_text      TEXT,                      -- what the tariff says
    review_status   TEXT NOT NULL DEFAULT 'none', -- none | review_requested | under_review | refunded | upheld
    txn_id          TEXT
);

CREATE TABLE documents (
    document_id     TEXT PRIMARY KEY,
    account_id      TEXT REFERENCES accounts(account_id),
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    doc_type        TEXT NOT NULL,             -- statement | archived_statement | transactions_export | account_confirmation | payment_confirmation | validation_report | acquiring_report | interest_certificate | closure_letter | complaint_acknowledgement | final_response
    period_start    TEXT,
    period_end      TEXT,
    status          TEXT NOT NULL,             -- available | requested | in_preparation | delivered_to_portal | not_available
    filename        TEXT,
    delivered_via   TEXT,
    created_at      TEXT
);

------------------------------------------------------------------------------
-- Business banking specifics
------------------------------------------------------------------------------

CREATE TABLE payment_batches (
    batch_id        TEXT PRIMARY KEY,          -- 'HV-042'
    business_id     TEXT NOT NULL REFERENCES businesses(business_id),
    batch_type      TEXT NOT NULL,             -- payroll | supplier | bulk_refund
    uploaded_by     TEXT REFERENCES business_users(user_id),
    uploaded_at     TEXT NOT NULL,
    file_name       TEXT,
    line_count      INTEGER,
    total_minor     INTEGER,
    validation_status TEXT NOT NULL,           -- received | passed | failed
    approval_status TEXT NOT NULL,             -- not_submitted | awaiting_first_approval | awaiting_second_approval | approved | rejected | expired
    execution_status TEXT NOT NULL,            -- not_executed | scheduled | executed | partially_executed
    execution_date  TEXT
);

CREATE TABLE batch_lines (
    batch_id        TEXT NOT NULL REFERENCES payment_batches(batch_id),
    line_no         INTEGER NOT NULL,
    payee_name      TEXT,
    sort_code       TEXT,
    account_number_masked TEXT,
    amount_minor    INTEGER,
    reference       TEXT,
    validation_result TEXT NOT NULL,           -- ok | missing_payee_label | invalid_sort_code | duplicate_line | over_limit
    line_status     TEXT NOT NULL,             -- pending | paid | rejected | held
    status_reason   TEXT,                      -- why rejected/held (internal unless stated otherwise)
    PRIMARY KEY (batch_id, line_no)
);

CREATE TABLE batch_approvals (
    batch_id        TEXT NOT NULL REFERENCES payment_batches(batch_id),
    user_id         TEXT NOT NULL REFERENCES business_users(user_id),
    step            INTEGER NOT NULL,
    decided_at      TEXT,
    decision        TEXT NOT NULL              -- approved | rejected | pending
);

CREATE TABLE access_requests (
    access_request_id TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL REFERENCES businesses(business_id),
    requested_by    TEXT,                      -- free text: who asked
    subject_name    TEXT NOT NULL,             -- person to add/remove
    action          TEXT NOT NULL,             -- add_user | grant_role | revoke_role | remove_user | limit_change
    role            TEXT,
    status          TEXT NOT NULL,             -- awaiting_administrator_approval | approved | rejected | completed
    status_at       TEXT
);

CREATE TABLE limit_change_requests (
    request_id      TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL REFERENCES businesses(business_id),
    current_limit_minor INTEGER,
    requested_limit_minor INTEGER,
    requested_by_user TEXT REFERENCES business_users(user_id),
    status          TEXT NOT NULL,             -- received | awaiting_signatory | approved | declined
    status_at       TEXT
);

CREATE TABLE acquiring_reports (
    report_id       TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL REFERENCES businesses(business_id),
    settlement_date TEXT NOT NULL,
    gross_minor     INTEGER,
    refunds_minor   INTEGER,
    chargebacks_minor INTEGER,
    fees_minor      INTEGER,
    net_minor       INTEGER,                   -- gross - refunds - chargebacks - fees
    status          TEXT NOT NULL,             -- ready | pending | delivered
    filename        TEXT
);

------------------------------------------------------------------------------
-- Complaints and service cases
------------------------------------------------------------------------------

CREATE TABLE complaints (
    complaint_id    TEXT PRIMARY KEY,          -- 'CMP-115'
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    received_at     TEXT NOT NULL,
    subject         TEXT NOT NULL,
    status          TEXT NOT NULL,             -- registered | acknowledged | under_investigation | final_response_issued | referred_to_ombudsman
    final_response_due TEXT,                   -- received_at + 8 weeks (DISP-like rule, fictionalised)
    ombudsman_rights_given INTEGER DEFAULT 0
);

-- Generic registrations made by service agents (HV-023 card-team case, etc.).
CREATE TABLE service_cases (
    service_case_id TEXT PRIMARY KEY,          -- 'HV-023'
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    team            TEXT NOT NULL,             -- card_team | payment_team | security_team | bereavement_team | specialist_support | complaints | data_protection | business_support
    opened_at       TEXT NOT NULL,
    subject         TEXT NOT NULL,
    status          TEXT NOT NULL,             -- registered | in_progress | closed
    finding         TEXT                       -- NULL until a finding exists
);

-- Data-protection requests (subject access, erasure, third-party disclosure).
CREATE TABLE data_requests (
    data_request_id TEXT PRIMARY KEY,
    customer_id     TEXT REFERENCES customers(customer_id),
    kind            TEXT NOT NULL,             -- subject_access | rectification | erasure | third_party_disclosure
    received_at     TEXT NOT NULL,
    due_at          TEXT,
    status          TEXT NOT NULL              -- registered | identity_check_pending | fulfilled | refused
);

------------------------------------------------------------------------------
-- Case corpus
------------------------------------------------------------------------------

CREATE TABLE cases (
    case_key        TEXT PRIMARY KEY,          -- 'SYN-0001'
    case_number     TEXT NOT NULL,             -- '0001' (folder name)
    scenario        TEXT NOT NULL,             -- 'transfer_status'
    family          TEXT NOT NULL,             -- payments | scheduled | cards | access | documents | profile | fees | business | safeguarding | complaints | fraud | out_of_scope
    variant         TEXT NOT NULL,
    title           TEXT NOT NULL,
    source_role     TEXT NOT NULL,
    status_line     TEXT NOT NULL,
    bank_id         TEXT NOT NULL REFERENCES banks(bank_id),
    customer_id     TEXT REFERENCES customers(customer_id),
    business_id     TEXT REFERENCES businesses(business_id),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    completed_at    TEXT,
    initial_request TEXT NOT NULL,
    overview        TEXT NOT NULL,
    next_action     TEXT NOT NULL,
    outcome         TEXT NOT NULL,
    difficulty      TEXT NOT NULL              -- routine | tricky | edge | adversarial
);

CREATE TABLE case_events (
    case_key        TEXT NOT NULL REFERENCES cases(case_key),
    seq             INTEGER NOT NULL,
    at              TEXT NOT NULL,
    channel         TEXT NOT NULL,             -- Secure portal | Secure chat | Verified call | Unverified call | Email | SMS | Internal note | Business portal | External message | Branch visit | Letter | App notification
    sender          TEXT NOT NULL,
    recipient       TEXT NOT NULL,
    body            TEXT NOT NULL,
    authenticated   INTEGER,                   -- 1 authenticated channel/session, 0 not, NULL n/a (internal)
    actor_kind      TEXT NOT NULL,             -- customer | third_party | bank_agent | bank_system | bank_team | external
    is_decision_visible INTEGER NOT NULL,      -- 1 if visible at the primary decision point
    PRIMARY KEY (case_key, seq)
);

CREATE TABLE case_attachments (
    case_key        TEXT NOT NULL REFERENCES cases(case_key),
    filename        TEXT NOT NULL,
    media_type      TEXT NOT NULL,
    first_event_seq INTEGER,                   -- event in which it first appears (availability time)
    description     TEXT,
    contains_untrusted_instructions INTEGER NOT NULL DEFAULT 0,
    sha256          TEXT,
    PRIMARY KEY (case_key, filename)
);

-- Ground truth for evaluation. One row per case.
CREATE TABLE case_labels (
    case_key        TEXT PRIMARY KEY REFERENCES cases(case_key),
    decision_after_event INTEGER NOT NULL,     -- events 1..N visible
    expected_path   TEXT NOT NULL,             -- lookup_and_relay | issue_document | register_and_route | confirm_before_change | submit_verified_instruction | redirect_to_secure_route | refer_specialist | decline_and_signpost | verify_then_act | no_action_explain
    first_action_type TEXT NOT NULL,           -- lookup | verify_identity_or_authority | register_case | request_document | send_for_customer_confirmation | submit_instruction | redirect_channel | refer_team | signpost_external | ask_clarifying_question | decline | block_card | reply_only
    first_action_target TEXT,                  -- system_id or party
    first_action_summary TEXT NOT NULL,
    required_gates  TEXT NOT NULL,             -- JSON list
    must_not        TEXT NOT NULL,             -- JSON list
    must_convey     TEXT NOT NULL,             -- JSON list: facts/limits the final message should carry
    not_established TEXT NOT NULL,             -- JSON list: facts the record does NOT support (anti-invention)
    signposts       TEXT NOT NULL,             -- JSON list: external routes that should be named, if any
    edge_tags       TEXT NOT NULL,             -- JSON list
    outcome_state   TEXT NOT NULL
);

-- Exactly what each bank system returns when the agent queries it for this case
-- (lets a simulator answer tool calls faithfully, and says what is NOT available).
CREATE TABLE case_system_responses (
    case_key        TEXT NOT NULL REFERENCES cases(case_key),
    system_id       TEXT NOT NULL REFERENCES systems(system_id),
    query_hint      TEXT NOT NULL,             -- what kind of query this answers
    response_text   TEXT NOT NULL,             -- verbatim record answer
    fields_available TEXT NOT NULL,            -- JSON list
    fields_absent   TEXT NOT NULL,             -- JSON list -> simulator should reply 'No further data returned.'
    PRIMARY KEY (case_key, system_id, query_hint)
);

-- Links from a case to the records it concerns.
CREATE TABLE case_records (
    case_key        TEXT NOT NULL REFERENCES cases(case_key),
    table_name      TEXT NOT NULL,
    record_id       TEXT NOT NULL,
    PRIMARY KEY (case_key, table_name, record_id)
);
