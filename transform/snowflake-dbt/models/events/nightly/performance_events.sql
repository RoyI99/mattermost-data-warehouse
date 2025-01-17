{{config({
    "materialized": "incremental",
    "schema": "events",
    "tags":"nightly",
    "snowflake_warehouse": "transform_xs"
  })
}}

{% set rudder_relations = get_rudder_relations(schema=["mm_telemetry_prod","mm_telemetry_rc"], database='RAW', 
                          table_inclusions="'event'") %}
{{ union_relations(relations = rudder_relations[0], tgt_relation = rudder_relations[1]) }}

