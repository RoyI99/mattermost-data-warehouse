{{config({
    "materialized": 'view',
    "schema": "hightouch"
  })
}}

with leads_to_insert as (
    select * from {{ ref('onprem_trial_request_inapp_facts') }}
    where not lead_exists and not contact_exists
)
select * from leads_to_insert