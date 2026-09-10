-- Source-derived occurrences, not observed properties of a specimen.
SELECT ca.uri AS assertion_uri,
       assignment.uri AS assignment_uri,
       concept.notation,
       ca.perspective_uri,
       ca.applicability_scope_uris_json,
       ca.source_record_uri,
       ca.source_predicate_uri,
       CASE WHEN endorsed.assertion_uri IS NULL THEN 0 ELSE 1 END
         AS directly_endorsed
FROM classification_assertions AS ca
JOIN classification_assignments AS assignment ON assignment.assertion_uri = ca.uri
JOIN concepts AS concept ON concept.uri = ca.classification_uri
LEFT JOIN endorsed_classification_assertions AS endorsed ON endorsed.assertion_uri = ca.uri
WHERE ca.target_uri = 'http://www.mimo-db.eu/InstrumentsKeywords/3111'
ORDER BY ca.uri;
