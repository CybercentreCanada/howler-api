from howler.odm import (
    IP,
    MAC,
    MD5,
    SHA1,
    SHA256,
    URI,
    UUID,
    Any,
    Boolean,
    Classification,
    ClassificationString,
    Date,
    Domain,
    Email,
    Enum,
    FlattenedObject,
    Float,
    Integer,
    Json,
    Keyword,
    LowerKeyword,
    PhoneNumber,
    Platform,
    Processor,
    SSDeepHash,
    Text,
    UpperKeyword,
    URIPath,
    ValidatedKeyword,
)

# Simple types can be resolved by a direct mapping
TYPE_MAPPING = {
    Keyword: "keyword",
    Boolean: "boolean",
    Integer: "integer",
    Float: "float",
    Date: "date",
    Text: "text",
    Classification: "keyword",
    ClassificationString: "keyword",
    Enum: "keyword",
    UUID: "keyword",
    IP: "ip",
    Domain: "keyword",
    Email: "keyword",
    URI: "keyword",
    URIPath: "keyword",
    MAC: "keyword",
    PhoneNumber: "keyword",
    SSDeepHash: "text",
    SHA1: "keyword",
    SHA256: "keyword",
    MD5: "keyword",
    Platform: "keyword",
    Processor: "keyword",
    FlattenedObject: "nested",
    Any: "keyword",
    UpperKeyword: "keyword",
    LowerKeyword: "keyword",
    Json: "keyword",
    ValidatedKeyword: "keyword",
}

ANALYZER_MAPPING = {
    SSDeepHash: "text_fuzzy",
}

NORMALIZER_MAPPING = {
    SHA1: "lowercase_normalizer",
    SHA256: "lowercase_normalizer",
    MD5: "lowercase_normalizer",
}

# TODO: We might want to use custom analyzers for Classification and Enum and not create special backmapping cases
BACK_MAPPING = {
    v: k
    for k, v in TYPE_MAPPING.items()
    if k
    not in [
        Enum,
        Classification,
        UUID,
        IP,
        Domain,
        URI,
        URIPath,
        MAC,
        PhoneNumber,
        SSDeepHash,
        Email,
        SHA1,
        SHA256,
        MD5,
        Platform,
        Processor,
        ClassificationString,
        Any,
        UpperKeyword,
        LowerKeyword,
        Json,
        ValidatedKeyword,
    ]
}

BACK_MAPPING.update({x: Keyword for x in set(ANALYZER_MAPPING.values())})
