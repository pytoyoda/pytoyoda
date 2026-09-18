"""Toyota Connected Services API - Vehicle Models."""

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import Field

from pytoyoda.models.endpoints.common import StatusModel
from pytoyoda.utils.models import CustomEndpointBaseModel


class _TranslationModel(CustomEndpointBaseModel):
    english: Any | None = None
    french: Any | None = None
    spanish: Any | None = None


class _CapabilitiesModel(CustomEndpointBaseModel):
    description: str | None = None
    display: bool | None = None
    display_name: Any | None = Field(alias="displayName", default=None)
    name: str | None = None
    translation: _TranslationModel | None = None


class _ExtendedCapabilitiesModel(CustomEndpointBaseModel):
    c_scheduling: bool | None = Field(alias="acScheduling", default=None)
    battery_status: bool | None = Field(alias="batteryStatus", default=None)
    bonnet_status: bool | None = Field(alias="bonnetStatus", default=None)
    bump_collisions: bool | None = Field(alias="bumpCollisions", default=None)
    buzzer_capable: bool | None = Field(alias="buzzerCapable", default=None)
    charge_management: bool | None = Field(alias="chargeManagement", default=None)
    climate_capable: bool | None = Field(alias="climateCapable", default=None)
    climate_temperature_control_full: bool | None = Field(
        alias="climateTemperatureControlFull", default=None
    )
    climate_temperature_control_limited: bool | None = Field(
        alias="climateTemperatureControlLimited", default=None
    )
    dashboard_warning_lights: bool | None = Field(
        alias="dashboardWarningLights", default=None
    )
    door_lock_unlock_capable: bool | None = Field(
        alias="doorLockUnlockCapable", default=None
    )
    drive_pulse: bool | None = Field(alias="drivePulse", default=None)
    ecare: bool | None = Field(alias="ecare", default=None)
    econnect_climate_capable: bool | None = Field(
        alias="econnectClimateCapable", default=None
    )
    econnect_vehicle_status_capable: bool | None = Field(
        alias="econnectVehicleStatusCapable", default=None
    )
    electric_pulse: bool | None = Field(alias="electricPulse", default=None)
    emergency_assist: bool | None = Field(alias="emergencyAssist", default=None)
    enhanced_security_system_capable: bool | None = Field(
        alias="enhancedSecuritySystemCapable", default=None
    )
    equipped_with_alarm: bool | None = Field(alias="equippedWithAlarm", default=None)
    ev_battery: bool | None = Field(alias="evBattery", default=None)
    ev_charge_stations_capable: bool | None = Field(
        alias="evChargeStationsCapable", default=None
    )
    fcv_stations_capable: bool | None = Field(alias="fcvStationsCapable", default=None)
    front_defogger: bool | None = Field(alias="frontDefogger", default=None)
    front_driver_door_lock_status: bool | None = Field(
        alias="frontDriverDoorLockStatus", default=None
    )
    front_driver_door_open_status: bool | None = Field(
        alias="frontDriverDoorOpenStatus", default=None
    )
    front_driver_door_window_status: bool | None = Field(
        alias="frontDriverDoorWindowStatus", default=None
    )
    front_driver_seat_heater: bool | None = Field(
        alias="frontDriverSeatHeater", default=None
    )
    front_driver_seat_ventilation: bool | None = Field(
        alias="frontDriverSeatVentilation", default=None
    )
    front_passenger_door_lock_status: bool | None = Field(
        alias="frontPassengerDoorLockStatus", default=None
    )
    front_passenger_door_open_status: bool | None = Field(
        alias="frontPassengerDoorOpenStatus", default=None
    )
    front_passenger_door_window_status: bool | None = Field(
        alias="frontPassengerDoorWindowStatus", default=None
    )
    front_passenger_seat_heater: bool | None = Field(
        alias="frontPassengerSeatHeater", default=None
    )
    front_passenger_seat_ventilation: bool | None = Field(
        alias="frontPassengerSeatVentilation", default=None
    )
    fuel_level_available: bool | None = Field(alias="fuelLevelAvailable", default=None)
    fuel_range_available: bool | None = Field(alias="fuelRangeAvailable", default=None)
    guest_driver: bool | None = Field(alias="guestDriver", default=None)
    hazard_capable: bool | None = Field(alias="hazardCapable", default=None)
    horn_capable: bool | None = Field(alias="hornCapable", default=None)
    hybrid_pulse: bool | None = Field(alias="hybridPulse", default=None)
    hydrogen_pulse: bool | None = Field(alias="hydrogenPulse", default=None)
    last_parked_capable: bool | None = Field(alias="lastParkedCapable", default=None)
    light_status: bool | None = Field(alias="lightStatus", default=None)
    lights_capable: bool | None = Field(alias="lightsCapable", default=None)
    manual_rear_windows: bool | None = Field(alias="manualRearWindows", default=None)
    mirror_heater: bool | None = Field(alias="mirrorHeater", default=None)
    moonroof: bool | None = Field(alias="moonroof", default=None)
    next_charge: bool | None = Field(alias="nextCharge", default=None)
    power_tailgate_capable: bool | None = Field(
        alias="powerTailgateCapable", default=None
    )
    power_windows_capable: bool | None = Field(
        alias="powerWindowsCapable", default=None
    )
    rear_defogger: bool | None = Field(alias="rearDefogger", default=None)
    rear_driver_door_lock_status: bool | None = Field(
        alias="rearDriverDoorLockStatus", default=None
    )
    rear_driver_door_open_status: bool | None = Field(
        alias="rearDriverDoorOpenStatus", default=None
    )
    rear_driver_door_window_status: bool | None = Field(
        alias="rearDriverDoorWindowStatus", default=None
    )
    rear_driver_seat_heater: bool | None = Field(
        alias="rearDriverSeatHeater", default=None
    )
    rear_driver_seat_ventilation: bool | None = Field(
        alias="rearDriverSeatVentilation", default=None
    )
    rear_hatch_rear_window: bool | None = Field(
        alias="rearHatchRearWindow", default=None
    )
    rear_passenger_door_lock_status: bool | None = Field(
        alias="rearPassengerDoorLockStatus", default=None
    )
    rear_passenger_door_open_status: bool | None = Field(
        alias="rearPassengerDoorOpenStatus", default=None
    )
    rear_passenger_door_window_status: bool | None = Field(
        alias="rearPassengerDoorWindowStatus", default=None
    )
    rear_passenger_seat_heater: bool | None = Field(
        alias="rearPassengerSeatHeater", default=None
    )
    rear_passenger_seat_ventilation: bool | None = Field(
        alias="rearPassengerSeatVentilation", default=None
    )
    remote_econnect_capable: bool | None = Field(
        alias="remoteEConnectCapable", default=None
    )
    remote_engine_start_stop: bool | None = Field(
        alias="remoteEngineStartStop", default=None
    )
    smart_key_status: bool | None = Field(alias="smartKeyStatus", default=None)
    steering_heater: bool | None = Field(alias="steeringHeater", default=None)
    stellantis_climate_capable: bool | None = Field(
        alias="stellantisClimateCapable", default=None
    )
    stellantis_vehicle_status_capable: bool | None = Field(
        alias="stellantisVehicleStatusCapable", default=None
    )
    sunroof: bool | None = Field(alias="sunroof", default=None)
    telemetry_capable: bool | None = Field(alias="telemetryCapable", default=None)
    trunk_lock_unlock_capable: bool | None = Field(
        alias="trunkLockUnlockCapable", default=None
    )
    try_and_play: bool | None = Field(alias="tryAndPlay", default=None)
    vehicle_diagnostic_capable: bool | None = Field(
        alias="vehicleDiagnosticCapable", default=None
    )
    vehicle_finder: bool | None = Field(alias="vehicleFinder", default=None)
    vehicle_status: bool | None = Field(alias="vehicleStatus", default=None)
    we_hybrid_capable: bool | None = Field(alias="weHybridCapable", default=None)
    weekly_charge: bool | None = Field(alias="weeklyCharge", default=None)


class _LinksModel(CustomEndpointBaseModel):
    body: str | None = None
    button_text: str | None = Field(alias="buttonText", default=None)
    image_url: str | None = Field(alias="imageUrl", default=None)
    link: str | None = None
    name: str | None = None


class _DcmModel(CustomEndpointBaseModel):  # Data connection model
    country_code: str | None = Field(alias="countryCode", default=None)
    destination: str | None = Field(alias="dcmDestination", default=None)
    grade: str | None = Field(alias="dcmGrade", default=None)
    car_model_year: str | None = Field(alias="dcmModelYear", default=None)
    supplier: str | None = Field(alias="dcmSupplier", default=None)
    supplier_name: str | None = Field(alias="dcmSupplierName", default=None)
    euicc_id: str | None = Field(alias="euiccid", default=None)
    hardware_type: str | None = Field(alias="hardwareType", default=None)
    vehicle_unit_terminal_number: str | None = Field(
        alias="vehicleUnitTerminalNumber", default=None
    )


class _HeadUnitModel(CustomEndpointBaseModel):
    description: Any | None = Field(alias="huDescription", default=None)
    generation: Any | None = Field(alias="huGeneration", default=None)
    version: Any | None = Field(alias="huVersion", default=None)
    mobile_platform_code: Any | None = Field(alias="mobilePlatformCode", default=None)
    multimedia_type: Any | None = Field(alias="multimediaType", default=None)


class _SubscriptionsModel(CustomEndpointBaseModel):
    auto_renew: bool | None = Field(alias="autoRenew", default=None)
    category: str | None = None
    components: Any | None = None
    consolidated_goodwill_ids: list[Any] | None = Field(
        alias="consolidatedGoodwillIds", default=None
    )
    consolidated_product_ids: list[Any] | None = Field(
        alias="consolidatedProductIds", default=None
    )
    display_procuct_name: str | None = Field(alias="displayProductName", default=None)
    display_term: str | None = Field(alias="displayTerm", default=None)
    future_cancel: bool | None = Field(alias="futureCancel", default=None)
    good_will_issued_for: Any | None = Field(alias="goodwillIssuedFor", default=None)
    product_code: str | None = Field(alias="productCode", default=None)
    product_description: str | None = Field(alias="productDescription", default=None)
    product_line: str | None = Field(alias="productLine", default=None)
    product_name: str | None = Field(alias="productName", default=None)
    procut_type: Any | None = Field(alias="productType", default=None)
    renewable: bool | None = None
    status: str | None = None
    subscription_end_date: date | None = Field(
        alias="subscriptionEndDate", default=None
    )
    subscription_id: str | None = Field(alias="subscriptionID", default=None)
    subscription_next_billing_date: Any | None = Field(
        alias="subscriptionNextBillingDate",
        default=None,
    )
    subscription_remaining_days: int | None = Field(
        alias="subscriptionRemainingDays", default=None
    )
    subscription_remaining_term: Any | None = Field(
        alias="subscriptionRemainingTerm",
        default=None,
    )
    subscription_start_date: date | None = Field(
        alias="subscriptionStartDate", default=None
    )
    subscription_term: str | None = Field(alias="subscriptionTerm", default=None)
    term: int | None = None
    term_unit: str | None = Field(alias="termUnit", default=None)
    type: str | None = None


class _RemoteServiceCapabilitiesModel(CustomEndpointBaseModel):
    acsetting_enabled: bool | None = Field(alias="acsettingEnabled", default=None)
    allow_hvac_override_capable: bool | None = Field(
        alias="allowHvacOverrideCapable", default=None
    )
    dlock_unlock_capable: bool | None = Field(alias="dlockUnlockCapable", default=None)
    estart_enabled: bool | None = Field(alias="estartEnabled", default=None)
    estart_stop_capable: bool | None = Field(alias="estartStopCapable", default=None)
    estop_enabled: bool | None = Field(alias="estopEnabled", default=None)
    guest_driver_capable: bool | None = Field(alias="guestDriverCapable", default=None)
    hazard_capable: bool | None = Field(alias="hazardCapable", default=None)
    head_light_capable: bool | None = Field(alias="headLightCapable", default=None)
    moon_roof_capable: bool | None = Field(alias="moonRoofCapable", default=None)
    power_window_capable: bool | None = Field(alias="powerWindowCapable", default=None)
    steering_wheel_heater_capable: bool | None = Field(
        alias="steeringWheelHeaterCapable", default=None
    )
    trunk_capable: bool | None = Field(alias="trunkCapable", default=None)
    vehicle_finder_capable: bool | None = Field(
        alias="vehicleFinderCapable", default=None
    )
    ventilator_capable: bool | None = Field(alias="ventilatorCapable", default=None)


class _DataConsentModel(CustomEndpointBaseModel):
    can_300: bool | None = Field(alias="can300", default=None)
    dealer_contact: bool | None = Field(alias="dealerContact", default=None)
    service_connect: bool | None = Field(alias="serviceConnect", default=None)
    ubi: bool | None = Field(alias="ubi", default=None)


class _FeaturesModel(CustomEndpointBaseModel):
    ach_payment: bool | None = Field(alias="achPayment", default=None)
    add_service_record: bool | None = Field(alias="addServiceRecord", default=None)
    auto_drive: bool | None = Field(alias="autoDrive", default=None)
    cerence: bool | None = Field(alias="cerence", default=None)
    charging_station: bool | None = Field(alias="chargingStation", default=None)
    climate_start_engine: bool | None = Field(alias="climateStartEngine", default=None)
    collision_assistance: bool | None = Field(alias="collisionAssistance", default=None)
    connected_card: bool | None = Field(alias="connectedCard", default=None)
    connected_insurance: bool | None = Field(alias="connectedInsurance", default=None)
    connected_support: bool | None = Field(alias="connectedSupport", default=None)
    crash_notification: bool | None = Field(alias="crashNotification", default=None)
    critical_alert: bool | None = Field(alias="criticalAlert", default=None)
    dashboard_lights: bool | None = Field(alias="dashboardLights", default=None)
    dealer_appointment: bool | None = Field(alias="dealerAppointment", default=None)
    digital_key: bool | None = Field(alias="digitalKey", default=None)
    door_lock_capable: bool | None = Field(alias="doorLockCapable", default=None)
    drive_pulse: bool | None = Field(alias="drivePulse", default=None)
    driver_companion: bool | None = Field(alias="driverCompanion", default=None)
    driver_score: bool | None = Field(alias="driverScore", default=None)
    dtc_access: bool | None = Field(alias="dtcAccess", default=None)
    dynamic_navi: bool | None = Field(alias="dynamicNavi", default=None)
    eco_history: bool | None = Field(alias="ecoHistory", default=None)
    eco_ranking: bool | None = Field(alias="ecoRanking", default=None)
    electric_pulse: bool | None = Field(alias="electricPulse", default=None)
    emergency_assist: bool | None = Field(alias="emergencyAssist", default=None)
    enhanced_security_system: bool | None = Field(
        alias="enhancedSecuritySystem", default=None
    )
    ev_charge_station: bool | None = Field(alias="evChargeStation", default=None)
    ev_remote_services: bool | None = Field(alias="evRemoteServices", default=None)
    ev_vehicle_status: bool | None = Field(alias="evVehicleStatus", default=None)
    financial_services: bool | None = Field(alias="financialServices", default=None)
    flex_rental: bool | None = Field(alias="flexRental", default=None)
    h2_fuel_station: bool | None = Field(alias="h2FuelStation", default=None)
    home_charge: bool | None = Field(alias="homeCharge", default=None)
    how_to_videos: bool | None = Field(alias="howToVideos", default=None)
    hybrid_pulse: bool | None = Field(alias="hybridPulse", default=None)
    hydrogen_pulse: bool | None = Field(alias="hydrogenPulse", default=None)
    important_message: bool | None = Field(alias="importantMessage", default=None)
    insurance: bool | None = Field(alias="insurance", default=None)
    last_parked: bool | None = Field(alias="lastParked", default=None)
    lcfs: bool | None = Field(alias="lcfs", default=None)
    linked_accounts: bool | None = Field(alias="linkedAccounts", default=None)
    maintenance_timeline: bool | None = Field(alias="maintenanceTimeline", default=None)
    marketing_card: bool | None = Field(alias="marketingCard", default=None)
    marketing_consent: bool | None = Field(alias="marketingConsent", default=None)
    master_consent_editable: bool | None = Field(
        alias="masterConsentEditable", default=None
    )
    my_destination: bool | None = Field(alias="myDestination", default=None)
    owners_manual: bool | None = Field(alias="ownersManual", default=None)
    paid_product: bool | None = Field(alias="paidProduct", default=None)
    parked_vehicle_locator: bool | None = Field(
        alias="parkedVehicleLocator", default=None
    )
    parking: bool | None = Field(alias="parking", default=None)
    parking_notes: bool | None = Field(alias="parkingNotes", default=None)
    personalized_settings: bool | None = Field(
        alias="personalizedSettings", default=None
    )
    privacy: bool | None = Field(alias="privacy", default=None)
    recent_trip: bool | None = Field(alias="recentTrip", default=None)
    remote_dtc: bool | None = Field(alias="remoteDtc", default=None)
    remote_parking: bool | None = Field(alias="remoteParking", default=None)
    remote_service: bool | None = Field(alias="remoteService", default=None)
    roadside_assistance: bool | None = Field(alias="roadsideAssistance", default=None)
    safety_recall: bool | None = Field(alias="safetyRecall", default=None)
    schedule_maintenance: bool | None = Field(alias="scheduleMaintenance", default=None)
    service_history: bool | None = Field(alias="serviceHistory", default=None)
    shop_genuine_parts: bool | None = Field(alias="shopGenuineParts", default=None)
    smart_charging: bool | None = Field(alias="smartCharging", default=None)
    ssa_download: bool | None = Field(alias="ssaDownload", default=None)
    sxm_radio: bool | None = Field(alias="sxmRadio", default=None)
    telemetry: bool | None = Field(alias="telemetry", default=None)
    tff: bool | None = Field(alias="tff", default=None)
    tire_pressure: bool | None = Field(alias="tirePressure", default=None)
    v1g: bool | None = Field(alias="v1g", default=None)
    va_setting: bool | None = Field(alias="vaSetting", default=None)
    vehicle_diagnostic: bool | None = Field(alias="vehicleDiagnostic", default=None)
    vehicle_health_report: bool | None = Field(
        alias="vehicleHealthReport", default=None
    )
    vehicle_specifications: bool | None = Field(
        alias="vehicleSpecifications", default=None
    )
    vehicle_status: bool | None = Field(alias="vehicleStatus", default=None)
    we_hybrid: bool | None = Field(alias="weHybrid", default=None)
    wifi: bool | None = Field(alias="wifi", default=None)
    xcapp: bool | None = Field(alias="xcapp", default=None)


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

    alerts: list[Any] | None = None
    asi_code: str | None = Field(alias="asiCode", default=None)
    brand: str | None = None
    capabilities: list[_CapabilitiesModel] | None = None
    car_line_name: str | None = Field(alias="carlineName", default=None)
    color: str | None = None
    commercial_rental: bool | None = Field(alias="commercialRental", default=None)
    contract_id: str | None = Field(alias="contractId", default=None)
    cts_links: _LinksModel | None = Field(alias="ctsLinks", default=None)
    data_consent: _DataConsentModel | None = Field(alias="dataConsent", default=None)
    date_of_first_use: date | None = Field(alias="dateOfFirstUse", default=None)
    dcm: _DcmModel | None = None
    dcm_active: bool | None = Field(alias="dcmActive", default=None)
    dcms: Any | None = None
    display_model_description: str | None = Field(
        alias="displayModelDescription", default=None
    )
    display_subscriptions: list[dict[str, str]] | None = Field(
        alias="displaySubscriptions", default=None
    )
    electrical_platform_code: str | None = Field(
        alias="electricalPlatformCode", default=None
    )
    emergency_contact: Any | None = Field(alias="emergencyContact", default=None)
    ev_vehicle: bool | None = Field(alias="evVehicle", default=None)
    extended_capabilities: _ExtendedCapabilitiesModel | None = Field(
        alias="extendedCapabilities", default=None
    )
    external_subscriptions: Any | None = Field(
        alias="externalSubscriptions", default=None
    )
    family_sharing: bool | None = Field(alias="familySharing", default=None)
    faq_url: str | None = Field(alias="faqUrl", default=None)
    features: _FeaturesModel | None = None
    fleet_ind: Any | None = Field(alias="fleetInd", default=None)
    fuel_type: str | None = Field(alias="fuelType", default=None)
    generation: str | None = None
    head_unit: _HeadUnitModel | None = Field(alias="headUnit", default=None)
    hw_type: Any | None = Field(alias="hwType", default=None)
    image: str | None = None
    imei: str | None = None
    katashiki_code: str | None = Field(alias="katashikiCode", default=None)
    manufactured_date: date | None = Field(alias="manufacturedDate", default=None)
    manufactured_code: str | None = Field(alias="manufacturerCode", default=None)
    car_model_code: str | None = Field(alias="modelCode", default=None)
    car_model_description: str | None = Field(alias="modelDescription", default=None)
    car_model_name: str | None = Field(alias="modelName", default=None)
    car_model_year: str | None = Field(alias="modelYear", default=None)
    nickname: str | None = Field(alias="nickName", default=None)
    non_cvt_vehicle: bool | None = Field(alias="nonCvtVehicle", default=None)
    old_imei: Any | None = Field(alias="oldImei", default=None)
    owner: bool | None = None
    personalized_settings: _LinksModel | None = Field(
        alias="personalizedSettings", default=None
    )
    preferred: bool | None = None
    primary_subscriber: bool | None = Field(alias="primarySubscriber", default=None)
    region: str | None = None
    registration_number: str | None = Field(alias="registrationNumber", default=None)
    remote_display: Any | None = Field(alias="remoteDisplay", default=None)
    remote_service_capabilities: _RemoteServiceCapabilitiesModel | None = Field(
        alias="remoteServiceCapabilities", default=None
    )
    remote_service_exceptions: list[Any] | None = Field(
        alias="remoteServicesExceptions", default=None
    )
    remote_subscription_exists: bool | None = Field(
        alias="remoteSubscriptionExists", default=None
    )
    remote_subscription_status: str | None = Field(
        alias="remoteSubscriptionStatus", default=None
    )
    remote_user: bool | None = Field(alias="remoteUser", default=None)
    remote_user_guid: UUID | str | None = Field(alias="remoteUserGuid", default=None)
    service_connect_status: Any | None = Field(
        alias="serviceConnectStatus", default=None
    )
    services: list[Any] | None = None
    shop_genuine_parts_url: str | None = Field(
        alias="shopGenuinePartsUrl", default=None
    )
    status: str | None = None
    stock_pic_reference: str | None = Field(alias="stockPicReference", default=None)
    subscriber_guid: UUID | None = Field(alias="subscriberGuid", default=None)
    subscription_expiration_status: bool | None = Field(
        alias="subscriptionExpirationStatus", default=None
    )
    subscription_status: str | None = Field(alias="subscriptionStatus", default=None)
    subscriptions: list[_SubscriptionsModel] | None = None
    suffix_code: Any | None = Field(alias="suffixCode", default=None)
    svl_satus: bool | None = Field(alias="svlStatus", default=None)
    tff_links: _LinksModel | None = Field(alias="tffLinks", default=None)
    transmission_type: str | None = Field(alias="transmissionType", default=None)
    vehicle_capabilities: list[Any] | None = Field(
        alias="vehicleCapabilities", default=None
    )
    vehicle_data_consents: Any | None = Field(alias="vehicleDataConsents", default=None)
    vin: str | None = None


class VehiclesResponseModel(StatusModel):
    r"""Model representing a vehicles response.

    Inherits from StatusModel.

    Attributes:
        payload (Optional[list[VehicleGuidModel]], optional): The vehicles payload.
            Defaults to None.

    """

    payload: list[VehicleGuidModel] | None = None
