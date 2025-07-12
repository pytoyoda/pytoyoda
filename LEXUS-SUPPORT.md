| Endpoint                                                                                 | Status                            |
| ---------------------------------------------------------------------------------------- | --------------------------------- |
| /v2/vehicle/guid                                                                         | ✅                                |
| /directions/v5/{user}/{profile}/{coordinates}                                            | 🔵 NOT_TESTED                     |
| /getKeyInfo/{keyInfoId}                                                                  | 🔵 NOT_TESTED                     |
| /guid/{guid}/vins                                                                        | 🔵 NOT_TESTED                     |
| /listKeyInfo/{deviceId}                                                                  | 🔵 NOT_TESTED                     |
| /mileage-verification/vin/{vin}                                                          | 🔵 404 NOT_FOUND                  |
| /oa21mm/v1/ota/update/check                                                              | ❌ 403 Unauthorized               |
| /oa21mm/v1/svc/guid/{guid}/vins                                                          | 🔵 NOT_TESTED                     |
| /oa21mm/v1/svc/musicpreference                                                           | ❌ 403 Unauthorized               |
| /oa21mm/v1/svc/subscriptions                                                             | ❌ 403 Unauthorized               |
| /oa21mm/v1/svc/sync/vapreference                                                         | ❌ 403 Unauthorized               |
| onetrust/consent/dataSubject/{id}                                                        | 🔵 NOT_TESTED                     |
| onetrust/consent/purposes/{id}                                                           | 🔵 NOT_TESTED                     |
| /orders                                                                                  | ❌ 400 Locale is missing          |
| /osb/slider                                                                              | ❌ 400 Bad Request                |
| /self-service/asset-device/mop/unlock-status                                             | ❌ 403 Unauthorized               |
| /tou/product/mapping                                                                     | ✅                                |
| /translations/xKQ1i33s9htHVN9fi994WJZUE/feed/{locale}                                    | 🔵 NOT_TESTED                     |
| /v1/account/emailsearch                                                                  | ❌ 403 Unauthorized               |
| /v1/campaigns                                                                            | ❌ 403 Unauthorized               |
| /v1/canbus/trip/events                                                                   | ❌ 403 Unauthorized               |
| /v1/collisiondata                                                                        | ❌ 403 Unauthorized               |
| /v1/customer/eligibility                                                                 | ❌ 403 Unauthorized               |
| /v1/dashboardlights                                                                      | ❌ 403 Unauthorized               |
| /v1/deeplink                                                                             | ❌ 403 Unauthorized               |
| /v1/destinations                                                                         | ❌ 400 Require header X-locale    |
| /v1/eligibility                                                                          | ❌ 403 Unauthorized               |
| /v1/external/vehicle-subscriptions                                                       | ❌ 415 Unsupported Media Type     |
| /v1/feedback/metadata                                                                    | ❌ 403 Unauthorized               |
| /v1/global/remote/ac-reservation                                                         | ✅                                |
| /v1/global/remote/climate-settings                                                       | ✅                                |
| /v1/global/remote/climate-status                                                         | ✅                                |
| /v1/global/remote/electric/status                                                        | 🔵 Capability not present         |
| /v1/global/remote/electric/realtime-status                                               | ❌ 403 Unauthorized               |
| /v1/global/remote/profile-settings                                                       | ❌ 403 Unauthorized               |
| /v1/global/remote/status                                                                 | ✅                                |
| /v1/home-charging/charge-boxes                                                           | 🔵 Capability not present         |
| /v1/home-charging/charge-boxes/energy-contract/country/{countryIso}/tariff-configuration | 🔵 Capability not present         |
| /v1/home-charging/charge-boxes/invitations                                               | 🔵 Capability not present         |
| /v1/home-charging/charge-boxes/{serialNumber}"                                           | 🔵 Capability not present         |
| /v1/home-charging/charge-boxes/{serialNumber}/charging-sessions-history                  | 🔵 Capability not present         |
| /v1/home-charging/charge-boxes/smart-charging/details                                    | 🔵 Capability not present         |
| /v1/immobiliser                                                                          | ✅                                |
| /v1/insurance/contracts                                                                  | ❌ 500 Internal server error      |
| /v1/insurance/fhi                                                                        | 🔵 404 NOT_FOUND                  |
| /v1/insurance/ubi                                                                        | 🔵 404 NOT_FOUND                  |
| /v1/insurance/ubi/trips                                                                  | 🔵 404 NOT_FOUND                  |
| /v1/irf/list                                                                             | ❌ 403 Unauthorized               |
| /v1/irf/search                                                                           | ❌ 403 Unauthorized               |
| /v1/legacy/remote/profile-settings                                                       | ❌ 403 Unauthorized               |
| /v1/license                                                                              | ❌ 403 Unauthorized               |
| /v1/location                                                                             | ✅                                |
| /v1/marketing/banner                                                                     | ❌ 403 Unauthorized               |
| /v1/mobile-utilites/app-details/android                                                  | ✅                                |
| /v1/mp/parking                                                                           | ❌ 403 Unauthorized               |
| /v1/mp/parking/booking/{bookingId}                                                       | 🔵 NOT_TESTED                     |
| /v1/mp/parking/booking/confirmation/{confirmationId}/                                    | 🔵 NOT_TESTED                     |
| /v1/mp/parking/booking/user/{userId}                                                     | 🔵 NOT_TESTED                     |
| /v1/mp/parking/dashboard/{userId}                                                        | 🔵 NOT_TESTED                     |
| /v1/mp/parking/help                                                                      | ❌ 403 Unauthorized               |
| /v1/mp/parking/{locationId}                                                              | 🔵 NOT_TESTED                     |
| /v1/mp/payment/wallet/{userId}                                                           | 🔵 NOT_TESTED                     |
| /v1/mp/profile/{userId}                                                                  | 🔵 NOT_TESTED                     |
| /v1/navigation                                                                           | 🔵 NOT_TESTED                     |
| /v1/one/dealers                                                                          | ❌ 400 Bad Request                |
| /v1/one/vehicle                                                                          | ✅                                |
| /v1/ota/update                                                                           | ❌ 403 Unauthorized               |
| /v1/ota/update/history/all                                                               | ❌ 403 Unauthorized               |
| /v1/ota/update/versions                                                                  | ❌ 403 Unauthorized               |
| /v1/poi-service/commands/vin/{vin}                                                       | ✅                                |
| /v1/poi-service/pois/contract/state                                                      | ❌ 400 Require header X-locale    |
| /v1/poi-service/pois/{id}                                                                | 🔵 NOT_TESTED                     |
| /1/poi-service/pois/{id}/rating                                                          | 🔵 NOT_TESTED                     |
| /v1/preferred-dealer                                                                     | ❌ 400 Bad Request                |
| /v1/radio                                                                                | ❌ 403 Unauthorized               |
| /v1/servicehistory/vehicle/summary                                                       | ❌ 500/401 Unauthorized           |
| /v1/sms/consent                                                                          | ❌ 403 Unauthorized               |
| /v1/subscriptions                                                                        | ❌ 403 Unauthorized               |
| /v1/token                                                                                | ✅                                |
| /v1/trips                                                                                | ✅                                |
| /v1/trips/preferences                                                                    | ✅                                |
| /v1/vdr/history                                                                          | ❌ 403 Unauthorized               |
| /v1/vehicle-alerts                                                                       | ❌ 403 Unauthorized               |
| /v1/vehicle/guidvins                                                                     | ❌ 403 Unauthorized               |
| /v1/vehiclehealth/report                                                                 | ❌ 403 Unauthorized               |
| /v1/vehiclehealth/status                                                                 | ✅                                |
| /v1/vehicle/maintenance-schedule                                                         | ❌ 403 Unauthorized               |
| /v1/vehicle-subscriptions                                                                | ❌ 500 Content-Type not supported |
| /v1/vehicle/vehicle-spec                                                                 | ❌ 403 Unauthorized               |
| /v1/vgi/eligibility                                                                      | ❌ 403 Unauthorized               |
| /v1/vhr/history                                                                          | ❌ 403 Unauthorized               |
| /v1/videos                                                                               | ❌ 403 Unauthorized               |
| /v1/wifistatus                                                                           | ❌ 403 Unauthorized               |
| /v1/zuora/payments                                                                       | ❌ 403 Unauthorized               |
| /v1/zuora/rsa-signature                                                                  | ❌ 403 Unauthorized               |
| /v2/dealer-service/appointments                                                          | ❌ 403 Unauthorized               |
| /v2/dealer-service/{dealerId}/advisors                                                   | 🔵 NOT_TESTED                     |
| /v2/dealer-service/{dealerId}/appointment/calendar/slots                                 | 🔵 NOT_TESTED                     |
| /v2/dealer-service/{dealerId}/appointment/slots                                          | 🔵 NOT_TESTED                     |
| /v2/dealer-service/{dealerId}/appointment/timeslot                                       | 🔵 NOT_TESTED                     |
| /v2/dealer-service/{dealerId}/services                                                   | 🔵 NOT_TESTED                     |
| /v2/dealer-service/{dealerId}/transportoptions                                           | 🔵 NOT_TESTED                     |
| /v2/download/ssa                                                                         | ❌ 403 Unauthorized               |
| /v2/manual/pdf/{documentURI}                                                             | 🔵 NOT_TESTED                     |
| /v2/manuals                                                                              | ❌ 403 Unauthorized               |
| /v2/marketing/cards                                                                      | ❌ 403 Unauthorized               |
| /v2/notification/history                                                                 | ✅                                |
| /v2/notification-preferences                                                             | ✅                                |
| /v2/rsa/contacts                                                                         | ✅                                |
| /v2/telemetry                                                                            | ❌ 403 Unauthorized               |
| /v3/account/secondaryUserName                                                            | ❌ 403 Unauthorized               |
| /v3/canbus/score                                                                         | ❌ 403 Unauthorized               |
| /v3/canbus/trip                                                                          | ❌ 403 Unauthorized               |
| /v3/telemetry                                                                            | ✅                                |
| /v4/account                                                                              | ✅                                |
| /v4/dealers/{dealerCode}                                                                 | 🔵 NOT_TESTED                     |
| /vehicleassociation/additionalInfo                                                       | ❌ 500 Internal server error      |
| vehicles/{vin}/privacy-mode                                                              | ✅                                |
