"""Fictional vocabulary pools. Nothing here refers to a real person or organisation."""

HOME_BANKS = [
    # bank_id, name, short, sort-code prefix, weight
    ("HV", "Harrow & Vale Bank plc", "H&V", "40", 80),
    ("CF", "Calder & Finch Bank plc", "C&F", "23", 10),
    ("NB", "Northmere Building Society", "NBS", "07", 10),
]

OTHER_BANKS = [
    "Brackenford Savings Bank", "Ostrel Bank", "Kestrel Mutual", "Lantern Quay Bank", "Pellmoor Bank",
    "Varden Credit Union", "Sallow Bank", "Thornwick Bank", "Easterly Bank", "Coldharbour Bank",
]
FOREIGN_BANKS = [
    ("Banca Ostrava Nord", "IT", "EUR"), ("Kessling Volksbank", "DE", "EUR"), ("Banque Ardenne Sud", "FR", "EUR"),
    ("Lisbeth Sparbank", "SE", "EUR"), ("Meridian Federal Savings", "US", "USD"), ("Pacifica Harbor Bank", "US", "USD"),
]

FIRST_F = ["Mara", "Elowen", "Nadia", "Mira", "Maeve", "Elena", "Nerys", "Leona", "Tamsin", "Isla", "Priya", "Amara",
           "Zainab", "Ingrid", "Sofia", "Hana", "Chiamaka", "Rosa", "Freya", "Ayesha", "Lucia", "Wren", "Agnieszka",
           "Mei", "Siobhan", "Yasmin", "Delphine", "Olamide", "Keziah", "Imogen"]
FIRST_M = ["Rowan", "Tobias", "Idris", "Callum", "Ewan", "Arjun", "Kofi", "Mateo", "Hamza", "Declan", "Oskar",
           "Rhys", "Tariq", "Jonah", "Felix", "Dariusz", "Kenji", "Emeka", "Luca", "Silas", "Ravi", "Bram",
           "Niall", "Yusuf", "Anton", "Gideon", "Teodor", "Malik", "Corin", "Hugo"]
FIRST_X = ["Ash", "Sasha", "Robin", "Jules", "Kit", "Sam", "Rory", "Alex"]
LAST = ["Ellison", "Ellery", "Marr", "Mercer", "Wren", "Rowan", "Calder", "Venn", "Fenwick", "Voss", "Rook",
        "Bell", "Marlow", "Ashdown", "Okafor", "Nakamura", "Haddad", "Kowalczyk", "Brennan", "Achterberg",
        "Delacroix", "Osei", "Varga", "Lindqvist", "Patel", "Quayle", "Thorne", "Hollis", "Abernethy", "Sallis",
        "Pereira", "Moreau", "Iqbal", "Castellan", "Dunmore", "Fairweather", "Greaves", "Halloran", "Imrie",
        "Jessop", "Kerridge", "Lennox", "Mbeki", "Nairn", "Ostrowski", "Pemberton", "Quint", "Ravel", "Sorensen",
        "Tremayne"]

TOWNS = [("Brackenford", "ZZ4 2ZZ"), ("Cedarford", "ZZ7 7ZZ"), ("Alderwick", "ZZ3 2ZZ"), ("Westmere", "ZZ1 5ZZ"),
         ("Harrowgate Vale", "ZZ9 1ZZ"), ("Lantern Quay", "ZZ2 4ZZ"), ("Fenwick Spur", "ZZ6 3ZZ"),
         ("Ossmere", "ZZ8 6ZZ"), ("Pellmoor", "ZZ5 8ZZ"), ("Thornwick", "ZZ0 9ZZ")]
STREETS = ["Maple Walk", "Cedar Walk", "Willow Walk", "Juniper Mews", "Hazel Walk", "Orchard Row", "Quarry Lane",
           "Kiln Street", "Mill Rise", "Ferry Road", "Lark Close", "Station Parade", "Granary Court", "Beacon Hill"]
EMAIL_DOMAINS = ["example.net", "mailbox.example", "post.example", "inbox.example"]

SMALL_BUSINESSES = ["Alder & Reed Workshop", "Westmere Garden Cooperative", "Fern & Finch Books",
                    "Kiln Street Ceramics", "Lark Close Lettings", "Pellmoor Joinery", "Ossmere Bike Repairs",
                    "Granary Court Dental", "Quarry Lane Plumbing", "Thornwick Tutors", "Beacon Hill Removals",
                    "Mill Rise Carpentry", "Juniper Mews Florist", "Station Parade Opticians",
                    "Harbour Light Upholstery", "Cobble & Thread Tailors", "Saltmarsh Garage",
                    "Brackenford Music School"]
MERCHANTS = ["Fern & Finch Books", "Corvid Coffee", "Lantern Grocers", "Pellmoor Fuel", "Northgate Electronics",
             "Ossmere Outdoor", "StreamNest Subscriptions", "Quayside Pharmacy", "Tallowmere Goods",
             "Brackenford Rail", "Kestrel Air", "Hollow Oak Hotel", "Marrow & Vine Restaurant",
             "Gildersleeve Online", "Spindle Fashion", "Rookery Pet Supplies"]
FOREIGN_MERCHANTS = [("Café Ostrava", "IT"), ("Kessling Mode", "DE"), ("Ardenne Hôtel", "FR"),
                     ("Pacifica Outfitters", "US"), ("Lisbeth Design", "SE")]
GYMS_ETC = ["Northmere Fitness", "Ossmere Energy", "Brackenford Water", "Cedarford Council Tax",
            "Lantern Broadband", "Pellmoor Mobile", "Westmere Insurance Services", "Kestrel Streaming",
            "Thornwick Housing Association", "Alderwick Leisure Club"]
COMPANIES = ["Fenwick Workshop Ltd", "Alder Quay Studio Ltd", "Merefield Design Studio Ltd", "Ossmere Freight Ltd",
             "Kiln Street Bakery Ltd", "Pellmoor Analytics Ltd", "Lantern Quay Events Ltd", "Brackenford Clinic LLP",
             "Thornwick Timber Ltd", "Saltmarsh Marine Supplies Ltd", "Corvid Coffee Roasters Ltd",
             "Halloran & Greaves Architects LLP"]
SECTORS = ["design", "hospitality", "construction", "retail", "logistics", "healthcare", "professional services"]
JOB_TITLES = ["Finance manager", "Director", "Office manager", "Bookkeeper", "Payroll officer", "Operations lead",
              "Accountant", "Company secretary"]
PURPOSES = ["bookcase", "garden fencing", "laptop repair", "deposit for a holiday cottage", "wedding photography",
            "rent contribution", "used car deposit", "kitchen worktop", "violin lessons", "tax adviser invoice",
            "sofa", "boiler service", "family gift", "tuition fees"]

# Bank systems and teams the agent can query or instruct.
SYSTEMS = [
    # id, label (prefixed with the bank short name in narrative), kind, read_only, description
    ("transfer_journal", "transfer journal", "record", 1, "Outgoing one-off transfers: status, timestamps, references, scheme, decline codes."),
    ("payment_instruction_journal", "payment instruction journal", "record", 1, "Instructions awaiting authorisation or scheduled for the future."),
    ("incoming_payment_system", "incoming-payment system", "record", 1, "Incoming credits, holds and returns."),
    ("transaction_journal", "account transaction journal", "record", 1, "Posted and pending account activity."),
    ("standing_order_journal", "standing-order journal", "record", 1, "Standing orders and run history."),
    ("dd_service", "Direct Debit service", "process", 0, "Mandates, collections, cancellations, indemnity claims."),
    ("card_system", "card management system", "record", 1, "Card status, dispatches, authorisations, restrictions."),
    ("card_team", "card team", "team", 0, "Card disputes, fraud reviews, chargebacks."),
    ("payment_team", "payment team", "team", 0, "Recalls, traces, investigations into payments."),
    ("security_team", "security team", "team", 0, "Scam reports, account takeover, suspicious contact."),
    ("authentication_service", "customer authentication service", "process", 1, "Session authentication results and step-up checks."),
    ("device_register", "mobile banking device register", "record", 1, "Registered devices and their status."),
    ("access_log", "sign-in log", "record", 1, "Sign-in events and access status."),
    ("profile_change_process", "secure profile-change process", "process", 0, "Changes to phone, address, name, email; requires customer confirmation."),
    ("document_service", "document service", "process", 0, "Statements, confirmations, exports, letters into the secure portal."),
    ("fee_tariff", "fee tariff record", "record", 1, "Fees charged and the tariff basis."),
    ("fee_review_process", "fee review process", "process", 0, "Customer requests to review a fee."),
    ("complaints_team", "complaints team", "team", 0, "Formal complaints, acknowledgements, final responses."),
    ("specialist_support", "specialist support team", "team", 0, "Customers in vulnerable circumstances; economic abuse; bereavement; financial difficulty."),
    ("bereavement_team", "bereavement team", "team", 0, "Deceased customers' accounts, executors and administrators."),
    ("third_party_register", "third-party authority register", "record", 1, "Powers of attorney, deputies, executors, additional cardholders."),
    ("data_protection_team", "data protection team", "team", 0, "Subject access and other data-protection requests."),
    ("business_role_register", "business role register", "record", 1, "Business users, roles, permissions and pending approvals."),
    ("business_access_process", "business access process", "process", 0, "Add/remove users and roles; needs the verified administrator."),
    ("import_service", "payment file import service", "process", 1, "Batch upload receipts and validation reports."),
    ("batch_approval_queue", "batch approval queue", "record", 1, "Approval steps and signatory status for batches."),
    ("limit_service", "payment limit service", "process", 0, "Business payment limits and change requests."),
    ("acquiring_reports", "merchant acquiring reporting", "record", 1, "Card-acceptance settlement reports."),
    ("cop_service", "payee name-check service", "record", 1, "Confirmation-of-payee style name-check results."),
    ("case_record", "case record", "record", 0, "The bank's own case log for this enquiry."),
    ("savings_products", "savings product record", "record", 1, "Product terms, rates, early-withdrawal charges."),
    ("collections_team", "financial support team", "team", 0, "Arrears, payment plans, breathing space."),
]
SYSTEM_LABELS = {s[0]: s[1] for s in SYSTEMS}
