"""Toyota Connected Services API - Vehicle Models."""

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _TranslationModel(CustomEndpointBaseModel):
    english: Any | None
    french: Any | None
    spanish: Any | None


class _CapabilitiesModel(CustomEndpointBaseModel):
    description: str | None
    display: bool | None
    display_name: Any | None = Field(alias="displayName")
    name: str | None
    translation: _TranslationModel | None


class _ExtendedCapabilitiesModel(CustomEndpointBaseModel):
    c_scheduling: bool | None = Field(alias="acScheduling")
    battery_status: bool | None = Field(alias="batteryStatus")
    bonnet_status: bool | None = Field(alias="bonnetStatus")
    bump_collisions: bool | None = Field(alias="bumpCollisions")
    buzzer_capable: bool | None = Field(alias="buzzerCapable")
    charge_management: bool | None = Field(alias="chargeManagement")
    climate_capable: bool | None = Field(alias="climateCapable")
    climate_temperature_control_full: bool | None = Field(
        alias="climateTemperatureControlFull"
    )
    climate_temperature_control_limited: bool | None = Field(
        alias="climateTemperatureControlLimited"
    )
    dashboard_warning_lights: bool | None = Field(alias="dashboardWarningLights")
    door_lock_unlock_capable: bool | None = Field(alias="doorLockUnlockCapable")
    drive_pulse: bool | None = Field(alias="drivePulse")
    ecare: bool | None = Field(alias="ecare")
    econnect_climate_capable: bool | None = Field(alias="econnectClimateCapable")
    econnect_vehicle_status_capable: bool | None = Field(
        alias="econnectVehicleStatusCapable"
    )
    electric_pulse: bool | None = Field(alias="electricPulse")
    emergency_assist: bool | None = Field(alias="emergencyAssist")
    enhanced_security_system_capable: bool | None = Field(
        alias="enhancedSecuritySystemCapable"
    )
    equipped_with_alarm: bool | None = Field(alias="equippedWithAlarm")
    ev_battery: bool | None = Field(alias="evBattery")
    ev_charge_stations_capable: bool | None = Field(alias="evChargeStationsCapable")
    fcv_stations_capable: bool | None = Field(alias="fcvStationsCapable")
    front_defogger: bool | None = Field(alias="frontDefogger")
    front_driver_door_lock_status: bool | None = Field(
        alias="frontDriverDoorLockStatus"
    )
    front_driver_door_open_status: bool | None = Field(
        alias="frontDriverDoorOpenStatus"
    )
    front_driver_door_window_status: bool | None = Field(
        alias="frontDriverDoorWindowStatus"
    )
    front_driver_seat_heater: bool | None = Field(alias="frontDriverSeatHeater")
    front_driver_seat_ventilation: bool | None = Field(
        alias="frontDriverSeatVentilation"
    )
    front_passenger_door_lock_status: bool | None = Field(
        alias="frontPassengerDoorLockStatus"
    )
    front_passenger_door_open_status: bool | None = Field(
        alias="frontPassengerDoorOpenStatus"
    )
    front_passenger_door_window_status: bool | None = Field(
        alias="frontPassengerDoorWindowStatus"
    )
    front_passenger_seat_heater: bool | None = Field(alias="frontPassengerSeatHeater")
    front_passenger_seat_ventilation: bool | None = Field(
        alias="frontPassengerSeatVentilation"
    )
    fuel_level_available: bool | None = Field(alias="fuelLevelAvailable")
    fuel_range_available: bool | None = Field(alias="fuelRangeAvailable")
    guest_driver: bool | None = Field(alias="guestDriver")
    hazard_capable: bool | None = Field(alias="hazardCapable")
    horn_capable: bool | None = Field(alias="hornCapable")
    hybrid_pulse: bool | None = Field(alias="hybridPulse")
    hydrogen_pulse: bool | None = Field(alias="hydrogenPulse")
    last_parked_capable: bool | None = Field(alias="lastParkedCapable")
    light_status: bool | None = Field(alias="lightStatus")
    lights_capable: bool | None = Field(alias="lightsCapable")
    manual_rear_windows: bool | None = Field(alias="manualRearWindows")
    mirror_heater: bool | None = Field(alias="mirrorHeater")
    moonroof: bool | None = Field(alias="moonroof")
    next_charge: bool | None = Field(alias="nextCharge")
    power_tailgate_capable: bool | None = Field(alias="powerTailgateCapable")
    power_windows_capable: bool | None = Field(alias="powerWindowsCapable")
    rear_defogger: bool | None = Field(alias="rearDefogger")
    rear_driver_door_lock_status: bool | None = Field(alias="rearDriverDoorLockStatus")
    rear_driver_door_open_status: bool | None = Field(alias="rearDriverDoorOpenStatus")
    rear_driver_door_window_status: bool | None = Field(
        alias="rearDriverDoorWindowStatus"
    )
    rear_driver_seat_heater: bool | None = Field(alias="rearDriverSeatHeater")
    rear_driver_seat_ventilation: bool | None = Field(alias="rearDriverSeatVentilation")
    rear_hatch_rear_window: bool | None = Field(alias="rearHatchRearWindow")
    rear_passenger_door_lock_status: bool | None = Field(
        alias="rearPassengerDoorLockStatus"
    )
    rear_passenger_door_open_status: bool | None = Field(
        alias="rearPassengerDoorOpenStatus"
    )
    rear_passenger_door_window_status: bool | None = Field(
        alias="rearPassengerDoorWindowStatus"
    )
    rear_passenger_seat_heater: bool | None = Field(alias="rearPassengerSeatHeater")
    rear_passenger_seat_ventilation: bool | None = Field(
        alias="rearPassengerSeatVentilation"
    )
    remote_econnect_capable: bool | None = Field(alias="remoteEConnectCapable")
    remote_engine_start_stop: bool | None = Field(alias="remoteEngineStartStop")
    smart_key_status: bool | None = Field(alias="smartKeyStatus")
    steering_heater: bool | None = Field(alias="steeringHeater")
    stellantis_climate_capable: bool | None = Field(alias="stellantisClimateCapable")
    stellantis_vehicle_status_capable: bool | None = Field(
        alias="stellantisVehicleStatusCapable"
    )
    sunroof: bool | None = Field(alias="sunroof")
    telemetry_capable: bool | None = Field(alias="telemetryCapable")
    trunk_lock_unlock_capable: bool | None = Field(alias="trunkLockUnlockCapable")
    try_and_play: bool | None = Field(alias="tryAndPlay")
    vehicle_diagnostic_capable: bool | None = Field(alias="vehicleDiagnosticCapable")
    vehicle_finder: bool | None = Field(alias="vehicleFinder")
    vehicle_status: bool | None = Field(alias="vehicleStatus")
    we_hybrid_capable: bool | None = Field(alias="weHybridCapable")
    weekly_charge: bool | None = Field(alias="weeklyCharge")


class _LinksModel(CustomEndpointBaseModel):
    body: str | None
    button_text: str | None = Field(alias="buttonText")
    image_url: str | None = Field(alias="imageUrl", default=None)
    link: str | None
    name: str | None


class _DcmModel(CustomEndpointBaseModel):  # Data connection model
    country_code: str | None = Field(alias="countryCode", default=None)
    destination: str | None = Field(alias="dcmDestination")
    grade: str | None = Field(alias="dcmGrade")
    car_model_year: str | None = Field(alias="dcmModelYear")
    supplier: str | None = Field(alias="dcmSupplier")
    supplier_name: str | None = Field(alias="dcmSupplierName", default=None)
    euicc_id: str | None = Field(alias="euiccid")
    hardware_type: str | None = Field(alias="hardwareType")
    vehicle_unit_terminal_number: str | None = Field(alias="vehicleUnitTerminalNumber")


class _HeadUnitModel(CustomEndpointBaseModel):
    description: Any | None = Field(alias="huDescription")
    generation: Any | None = Field(alias="huGeneration")
    version: Any | None = Field(alias="huVersion")
    mobile_platform_code: Any | None = Field(alias="mobilePlatformCode")
    multimedia_type: Any | None = Field(alias="multimediaType")


class _SubscriptionsModel(CustomEndpointBaseModel):
    auto_renew: bool | None = Field(alias="autoRenew")
    category: str | None
    components: Any | None
    consolidated_goodwill_ids: list[Any] | None = Field(alias="consolidatedGoodwillIds")
    consolidated_product_ids: list[Any] | None = Field(alias="consolidatedProductIds")
    display_procuct_name: str | None = Field(alias="displayProductName")
    display_term: str | None = Field(alias="displayTerm")
    future_cancel: bool | None = Field(alias="futureCancel")
    good_will_issued_for: Any | None = Field(alias="goodwillIssuedFor")
    product_code: str | None = Field(alias="productCode")
    product_description: str | None = Field(alias="productDescription")
    product_line: str | None = Field(alias="productLine")
    product_name: str | None = Field(alias="productName")
    procut_type: Any | None = Field(alias="productType")
    renewable: bool | None
    status: str | None
    subscription_end_date: date | None = Field(alias="subscriptionEndDate")
    subscription_id: str | None = Field(alias="subscriptionID")
    subscription_next_billing_date: Any | None = Field(
        alias="subscriptionNextBillingDate",
    )
    subscription_remaining_days: int | None = Field(alias="subscriptionRemainingDays")
    subscription_remaining_term: Any | None = Field(
        alias="subscriptionRemainingTerm",
    )
    subscription_start_date: date | None = Field(alias="subscriptionStartDate")
    subscription_term: str | None = Field(alias="subscriptionTerm")
    term: int | None
    term_unit: str | None = Field(alias="termUnit")
    type: str | None


class _RemoteServiceCapabilitiesModel(CustomEndpointBaseModel):
    acsetting_enabled: bool | None = Field(alias="acsettingEnabled")
    allow_hvac_override_capable: bool | None = Field(alias="allowHvacOverrideCapable")
    dlock_unlock_capable: bool | None = Field(alias="dlockUnlockCapable")
    estart_enabled: bool | None = Field(alias="estartEnabled")
    estart_stop_capable: bool | None = Field(alias="estartStopCapable")
    estop_enabled: bool | None = Field(alias="estopEnabled")
    guest_driver_capable: bool | None = Field(alias="guestDriverCapable")
    hazard_capable: bool | None = Field(alias="hazardCapable")
    head_light_capable: bool | None = Field(alias="headLightCapable")
    moon_roof_capable: bool | None = Field(alias="moonRoofCapable")
    power_window_capable: bool | None = Field(alias="powerWindowCapable")
    steering_wheel_heater_capable: bool | None = Field(
        alias="steeringWheelHeaterCapable"
    )
    trunk_capable: bool | None = Field(alias="trunkCapable")
    vehicle_finder_capable: bool | None = Field(alias="vehicleFinderCapable")
    ventilator_capable: bool | None = Field(alias="ventilatorCapable")


class _DataConsentModel(CustomEndpointBaseModel):
    can_300: bool | None = Field(alias="can300")
    dealer_contact: bool | None = Field(alias="dealerContact")
    service_connect: bool | None = Field(alias="serviceConnect")
    ubi: bool | None = Field(alias="ubi")


class _FeaturesModel(CustomEndpointBaseModel):
    ach_payment: bool | None = Field(alias="achPayment")
    add_service_record: bool | None = Field(alias="addServiceRecord")
    auto_drive: bool | None = Field(alias="autoDrive")
    cerence: bool | None = Field(alias="cerence")
    charging_station: bool | None = Field(alias="chargingStation")
    climate_start_engine: bool | None = Field(alias="climateStartEngine")
    collision_assistance: bool | None = Field(alias="collisionAssistance")
    connected_card: bool | None = Field(alias="connectedCard")
    connected_insurance: bool | None = Field(alias="connectedInsurance")
    connected_support: bool | None = Field(alias="connectedSupport")
    crash_notification: bool | None = Field(alias="crashNotification")
    critical_alert: bool | None = Field(alias="criticalAlert")
    dashboard_lights: bool | None = Field(alias="dashboardLights")
    dealer_appointment: bool | None = Field(alias="dealerAppointment")
    digital_key: bool | None = Field(alias="digitalKey")
    door_lock_capable: bool | None = Field(alias="doorLockCapable")
    drive_pulse: bool | None = Field(alias="drivePulse")
    driver_companion: bool | None = Field(alias="driverCompanion")
    driver_score: bool | None = Field(alias="driverScore")
    dtc_access: bool | None = Field(alias="dtcAccess")
    dynamic_navi: bool | None = Field(alias="dynamicNavi")
    eco_history: bool | None = Field(alias="ecoHistory")
    eco_ranking: bool | None = Field(alias="ecoRanking")
    electric_pulse: bool | None = Field(alias="electricPulse")
    emergency_assist: bool | None = Field(alias="emergencyAssist")
    enhanced_security_system: bool | None = Field(alias="enhancedSecuritySystem")
    ev_charge_station: bool | None = Field(alias="evChargeStation")
    ev_remote_services: bool | None = Field(alias="evRemoteServices")
    ev_vehicle_status: bool | None = Field(alias="evVehicleStatus")
    financial_services: bool | None = Field(alias="financialServices")
    flex_rental: bool | None = Field(alias="flexRental")
    h2_fuel_station: bool | None = Field(alias="h2FuelStation")
    home_charge: bool | None = Field(alias="homeCharge")
    how_to_videos: bool | None = Field(alias="howToVideos")
    hybrid_pulse: bool | None = Field(alias="hybridPulse")
    hydrogen_pulse: bool | None = Field(alias="hydrogenPulse")
    important_message: bool | None = Field(alias="importantMessage")
    insurance: bool | None = Field(alias="insurance")
    last_parked: bool | None = Field(alias="lastParked")
    lcfs: bool | None = Field(alias="lcfs")
    linked_accounts: bool | None = Field(alias="linkedAccounts")
    maintenance_timeline: bool | None = Field(alias="maintenanceTimeline")
    marketing_card: bool | None = Field(alias="marketingCard")
    marketing_consent: bool | None = Field(alias="marketingConsent")
    master_consent_editable: bool | None = Field(alias="masterConsentEditable")
    my_destination: bool | None = Field(alias="myDestination")
    owners_manual: bool | None = Field(alias="ownersManual")
    paid_product: bool | None = Field(alias="paidProduct")
    parked_vehicle_locator: bool | None = Field(alias="parkedVehicleLocator")
    parking: bool | None = Field(alias="parking")
    parking_notes: bool | None = Field(alias="parkingNotes")
    personalized_settings: bool | None = Field(alias="personalizedSettings")
    privacy: bool | None = Field(alias="privacy")
    recent_trip: bool | None = Field(alias="recentTrip")
    remote_dtc: bool | None = Field(alias="remoteDtc")
    remote_parking: bool | None = Field(alias="remoteParking")
    remote_service: bool | None = Field(alias="remoteService")
    roadside_assistance: bool | None = Field(alias="roadsideAssistance")
    safety_recall: bool | None = Field(alias="safetyRecall")
    schedule_maintenance: bool | None = Field(alias="scheduleMaintenance")
    service_history: bool | None = Field(alias="serviceHistory")
    shop_genuine_parts: bool | None = Field(alias="shopGenuineParts")
    smart_charging: bool | None = Field(alias="smartCharging")
    ssa_download: bool | None = Field(alias="ssaDownload")
    sxm_radio: bool | None = Field(alias="sxmRadio")
    telemetry: bool | None = Field(alias="telemetry")
    tff: bool | None = Field(alias="tff")
    tire_pressure: bool | None = Field(alias="tirePressure")
    v1g: bool | None = Field(alias="v1g")
    va_setting: bool | None = Field(alias="vaSetting")
    vehicle_diagnostic: bool | None = Field(alias="vehicleDiagnostic")
    vehicle_health_report: bool | None = Field(alias="vehicleHealthReport")
    vehicle_specifications: bool | None = Field(alias="vehicleSpecifications")
    vehicle_status: bool | None = Field(alias="vehicleStatus")
    we_hybrid: bool | None = Field(alias="weHybrid")
    wifi: bool | None = Field(alias="wifi")
    xcapp: bool | None = Field(alias="xcapp")


class VehicleGuidModel(CustomEndpointBaseModel):
    """Model representing a vehicle with its associated information.

    Attributes:
        alerts (list[Any]): The alerts associated with the vehicle.
        asiCode (str): The ASI code of the vehicle.
        brand (str): The brand of the vehicle.
        capabilities (list[_CapabilitiesModel]): The capabilities of the vehicle.
        car_line_name (str): The name of the car line.
        color (str): The color of the vehicle.
        commercial_rental (bool): Indicates if the vehicle is used for
            commercial rental.
        contract_id (str): The contract ID of the vehicle.
        cts_links (_LinksModel): The CTS (Connected Technologies Services) links
            of the vehicle.
        data_consent (_DataConsentModel): The data consent information of the vehicle.
        date_of_first_use (Optional[date]): The date of first use of the vehicle.
        dcm (_DcmModel): The DCM (Data Communication Module) information of the vehicle.
        dcm_active (bool): Indicates if the DCM is active for the vehicle.
        dcms (Optional[Any]): The DCMS (Data Communication Module Status) information
            of the vehicle.
        display_model_description (str): The description of the displayed model.
        display_subscriptions (list[dict[str, str]]): The displayed subscriptions
            of the vehicle.
        electrical_platform_code (str): The electrical platform code of the vehicle.
        emergency_contact (Optional[Any]): The emergency contact information
            of the vehicle.
        ev_vehicle (bool): Indicates if the vehicle is an electric vehicle.
        extended_capabilities (_ExtendedCapabilitiesModel): The extended capabilities
            of the vehicle.
        external_subscriptions (Optional[Any]): The external subscriptions
            of the vehicle.
        family_sharing (bool): Indicates if the vehicle is part of a family
            sharing plan.
        faq_url (str): The URL of the FAQ (Frequently Asked Questions) for the vehicle.
        features (_FeaturesModel): The features of the vehicle.
        fleet_ind (Optional[Any]): The fleet indicator of the vehicle.
        generation (str): The generation of the vehicle.
        head_unit (_HeadUnitModel): The head unit information of the vehicle.
        hw_type (Optional[Any]): The hardware type of the vehicle.
        image (str): The image URL of the vehicle.
        imei (str): The IMEI (International Mobile Equipment Identity) of the vehicle.
        katashiki_code (str): The katashiki code of the vehicle.
        manufactured_date (date): The manufactured date of the vehicle.
        manufactured_code (str): The manufacturer code of the vehicle.
        car_model_code (str): The model code of the vehicle.
        car_model_description (str): The description of the model of the vehicle.
        car_model_name (str): The name of the model of the vehicle.
        car_model_year (str): The model year of the vehicle.
        nickname (Optional[str]): The nickname of the vehicle.
        non_cvt_vehicle (bool): Indicates if the vehicle is a non-CVT
            (Continuously Variable Transmission) vehicle.
        old_imei (Optional[Any]): The old IMEI of the vehicle.
        owner (bool): Indicates if the user is the owner of the vehicle.
        personalized_settings (_LinksModel): The personalized settings of the vehicle.
        preferred (Optional[bool]): Indicates if the vehicle is the preferred vehicle.
        primary_subscriber (bool): Indicates if the user is the primary subscriber
            of the vehicle.
        region (str): The region of the vehicle.
        registration_number (Optional[str]): The registration number of the vehicle.
        remote_display (Optional[Any]): The remote display information of the vehicle.
        remote_service_capabilities (_RemoteServiceCapabilitiesModel): The remote
            service capabilities of the vehicle.
        remote_service_exceptions (list[Any]): The remote service exception
            of the vehicle.
        remote_subscription_exists (bool): Indicates if a remote subscription
            exists for the vehicle.
        remote_subscription_status (str): The remote subscription status of the vehicle.
        remote_user (bool): Indicates if the user is a remote user of the vehicle.
        remote_user_guid (Optional[Union[UUID, str]]): The remote user GUID
            (Globally Unique Identifier) of the vehicle.
        service_connect_status (Optional[Any]): The service connect status
            of the vehicle.
        services (list[Any]): The services associated with the vehicle.
        shop_genuine_parts_url (str): The URL for shopping genuine
            parts for the vehicle.
        status (str): The status of the vehicle.
        stock_pic_reference (str): The stock picture reference of the vehicle.
        subscriber_guid (UUID): The subscriber GUID of the vehicle.
        subscription_expiration_status (bool): Indicates if the subscription
            is expired for the vehicle.
        subscription_status (str): The subscription status of the vehicle.
        subscriptions (list[_SubscriptionsModel]): The subscriptions associated
            with the vehicle.
        suffix_code (Optional[Any]): The suffix code of the vehicle.
        svl_satus (bool): Indicates the SVL (Smart Vehicle Link) status of the vehicle.
        tff_links (_LinksModel): The TFF (Toyota Friend Finder) links of the vehicle.
        transmission_type (str): The transmission type of the vehicle.
        vehicle_capabilities (list[Any]): The capabilities of the vehicle.
        vehicle_data_consents (Optional[Any]): The vehicle data consents of the vehicle.
        vin (str): The VIN (Vehicle Identification Number) of the vehicle.

    """

    alerts: list[Any] | None
    asi_code: str | None = Field(alias="asiCode")
    brand: str | None
    capabilities: list[_CapabilitiesModel] | None
    car_line_name: str | None = Field(alias="carlineName")
    color: str | None
    commercial_rental: bool | None = Field(alias="commercialRental")
    contract_id: str | None = Field(alias="contractId")
    cts_links: _LinksModel | None = Field(alias="ctsLinks")
    data_consent: _DataConsentModel | None = Field(alias="dataConsent")
    date_of_first_use: date | None = Field(alias="dateOfFirstUse")
    dcm: _DcmModel | None = None
    dcm_active: bool | None = Field(alias="dcmActive")
    dcms: Any | None
    display_model_description: str | None = Field(alias="displayModelDescription")
    display_subscriptions: list[dict[str, str]] | None = Field(
        alias="displaySubscriptions"
    )
    electrical_platform_code: str | None = Field(
        alias="electricalPlatformCode", default=None
    )
    emergency_contact: Any | None = Field(alias="emergencyContact")
    ev_vehicle: bool | None = Field(alias="evVehicle")
    extended_capabilities: _ExtendedCapabilitiesModel | None = Field(
        alias="extendedCapabilities"
    )
    external_subscriptions: Any | None = Field(alias="externalSubscriptions")
    family_sharing: bool | None = Field(alias="familySharing")
    faq_url: str | None = Field(alias="faqUrl")
    features: _FeaturesModel | None
    fleet_ind: Any | None = Field(alias="fleetInd")
    fuel_type: str | None = Field(alias="fuelType", default=None)
    generation: str | None
    head_unit: _HeadUnitModel | None = Field(alias="headUnit")
    hw_type: Any | None = Field(alias="hwType")
    image: str | None
    imei: str | None = None
    katashiki_code: str | None = Field(alias="katashikiCode")
    manufactured_date: date | None = Field(alias="manufacturedDate")
    manufactured_code: str | None = Field(alias="manufacturerCode")
    car_model_code: str | None = Field(alias="modelCode")
    car_model_description: str | None = Field(alias="modelDescription")
    car_model_name: str | None = Field(alias="modelName")
    car_model_year: str | None = Field(alias="modelYear")
    nickname: str | None = Field(alias="nickName", default=None)
    non_cvt_vehicle: bool | None = Field(alias="nonCvtVehicle")
    old_imei: Any | None = Field(alias="oldImei", default=None)
    owner: bool | None
    personalized_settings: _LinksModel | None = Field(alias="personalizedSettings")
    preferred: bool | None = None
    primary_subscriber: bool | None = Field(alias="primarySubscriber")
    region: str | None
    registration_number: str | None = Field(alias="registrationNumber")
    remote_display: Any | None = Field(alias="remoteDisplay")
    remote_service_capabilities: _RemoteServiceCapabilitiesModel | None = Field(
        alias="remoteServiceCapabilities"
    )
    remote_service_exceptions: list[Any] | None = Field(
        alias="remoteServicesExceptions"
    )
    remote_subscription_exists: bool | None = Field(alias="remoteSubscriptionExists")
    remote_subscription_status: str | None = Field(alias="remoteSubscriptionStatus")
    remote_user: bool | None = Field(alias="remoteUser")
    remote_user_guid: UUID | str | None = Field(alias="remoteUserGuid", default=None)
    service_connect_status: Any | None = Field(alias="serviceConnectStatus")
    services: list[Any] | None
    shop_genuine_parts_url: str | None = Field(alias="shopGenuinePartsUrl")
    status: str | None
    stock_pic_reference: str | None = Field(alias="stockPicReference")
    subscriber_guid: UUID | None = Field(alias="subscriberGuid")
    subscription_expiration_status: bool | None = Field(
        alias="subscriptionExpirationStatus"
    )
    subscription_status: str | None = Field(alias="subscriptionStatus")
    subscriptions: list[_SubscriptionsModel] | None
    suffix_code: Any | None = Field(alias="suffixCode")
    svl_satus: bool | None = Field(alias="svlStatus")
    tff_links: _LinksModel | None = Field(alias="tffLinks")
    transmission_type: str | None = Field(alias="transmissionType")
    vehicle_capabilities: list[Any] | None = Field(alias="vehicleCapabilities")
    vehicle_data_consents: Any | None = Field(alias="vehicleDataConsents")
    vin: str | None


class VehiclesResponseModel(StatusModel):
    r"""Model representing a vehicles response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[list[VehicleGuidModel]], optional): The vehicles payload.
            Defaults to None.

    """

    payload: list[VehicleGuidModel] | None = None
