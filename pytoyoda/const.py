"""Toyota Connected Services API constants."""

# Misc
CLIENT_VERSION = "2.14.0"

# API URLs
API_BASE_URL = "HTTPS://ctpa-oneapi.tceu-ctp-prd.toyotaconnectedeurope.io"
ACCESS_TOKEN_URL = (
    "HTTPS://b2c-login.toyota-europe.com/oauth2/realms/root/realms/tme/access_token"  # noqa : S105
)
AUTHENTICATE_URL = "HTTPS://b2c-login.toyota-europe.com/json/realms/root/realms/tme/authenticate?authIndexType=service&authIndexValue=oneapp"
AUTHORIZE_URL = "HTTPS://b2c-login.toyota-europe.com/oauth2/realms/root/realms/tme/authorize?client_id=oneapp&scope=openid+profile+write&response_type=code&redirect_uri=com.toyota.oneapp:/oauth2Callback&code_challenge=plain&code_challenge_method=plain"

# Endpoint URLs
CUSTOMER_ACCOUNT_ENDPOINT = "TBD"
VEHICLE_ASSOCIATION_ENDPOINT = "/v1/vehicle-association/vehicle"
VEHICLE_GUID_ENDPOINT = "/v2/vehicle/guid"
VEHICLE_LOCATION_ENDPOINT = "/v1/location"
VEHICLE_HEALTH_STATUS_ENDPOINT = "/v1/vehiclehealth/status"
# Migrated 2026-07: Toyota retired /v1/global/remote/status (now fenced behind
# AWS SigV4 -> returns APIGW-403). The live app reads status from /v1/vehicle/status
# on the plain-Bearer authorizer. Const name kept to avoid churn in api.py.
VEHICLE_GLOBAL_REMOTE_STATUS_ENDPOINT = "/v1/vehicle/status"
# Migrated 2026-07: the status wake moved off the retired /v1/global/remote/*
# family (now SigV4-fenced -> APIGW-403) to the plain-Bearer /v1/remote/* refresh
# namespace, mirroring the already-migrated climate wake. The new route takes no
# body (vin header only) and returns payload.returnCode "000000" on accept.
# Const name kept to avoid churn in api.py.
VEHICLE_GLOBAL_REMOTE_REFRESH_STATUS_ENDPOINT = "/v1/remote/status"
VEHICLE_GLOBAL_REMOTE_ELECTRIC_STATUS_ENDPOINT = "/v1/global/remote/electric/status"
VEHICLE_GLOBAL_REMOTE_ELECTRIC_REALTIME_STATUS_ENDPOINT = (
    "/v1/global/remote/electric/realtime-status"
)
VEHICLE_GLOBAL_REMOTE_ELECTRIC_CONTROL_ENDPOINT = "/v1/global/remote/electric/command"
VEHICLE_TELEMETRY_ENDPOINT = "/v3/telemetry"
VEHICLE_NOTIFICATION_HISTORY_ENDPOINT = "/v2/notification/history"
VEHICLE_TRIPS_ENDPOINT = "/v1/trips?from={from_date}&to={to_date}&route={route}&summary={summary}&limit={limit}&offset={offset}"  # noqa: E501
VEHICLE_SERVICE_HISTORY_ENDPONT = "/v1/servicehistory/vehicle/summary"
# Migrated 2026-07: Toyota retired the /v1/global/remote/climate-* read routes
# (now behind AWS SigV4 -> APIGW-403). The live MyToyota app reads climate from
# the plain-Bearer /v1/vehicle/climate-* namespace and wakes via /v1/remote/*.
# Actuation (climate-control) moves to POST /v2/remote/climate-control with a new
# body (V2RemoteClimateControlRequest) and is migrated separately.
VEHICLE_CLIMATE_CONTROL_ENDPOINT = "/v1/global/remote/climate-control"
VEHICLE_CLIMATE_SETTINGS_ENDPOINT = "/v1/vehicle/climate-settings"
# The settings *write* (update_climate_settings) still targets the retired
# /v1/global/remote route. That route is already SigV4-fenced, so the write is
# non-functional regardless; it is removed with the actuation migration. Split from
# the read const above so this change moves only the read.
VEHICLE_CLIMATE_SETTINGS_WRITE_ENDPOINT = "/v1/global/remote/climate-settings"
VEHICLE_CLIMATE_STATUS_ENDPOINT = "/v1/vehicle/climate-status"
VEHICLE_CLIMATE_STATUS_REFRESH_ENDPOINT = "/v1/remote/refresh-climate-status"
VEHICLE_COMMAND_ENDPOINT = "/v1/global/remote/command"

# Units
KILOMETERS_UNIT = "km"
MILES_UNIT = "mi"
L_TO_MPG_FACTOR = 235.215
ML_TO_L_FACTOR = 1000.0
ML_TO_GAL_FACTOR = 3785.0
KM_TO_MILES_FACTOR = 0.621371192
MILES_TO_KM_FACTOR = 1.60934
