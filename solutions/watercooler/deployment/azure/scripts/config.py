#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT license. See LICENSE file in the project root for full license information.

import getpass
import json
import os
import pickle
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from os import path
from os.path import expanduser
import pathlib

from watercooler_utils import common
from watercooler_utils.common import lex_hash


class InstallConfiguration:
    __dump_file_name = expanduser("~") + "/.wc/wc_params.p"
    __backup_artifacts_path = expanduser("~") + "/wc/scripts/artifacts/"
    __artifacts_path = str(pathlib.Path(__file__).parent.absolute()) + "/artifacts/"

    """
        List of parameters we need guarantee uniqueness, 
        InstallConfiguration will suffix its default with hash based on deployment name 
    """
    __unique_properties = [
        "sqlserver.name",
        "keyvault.name",
        "m365Adf-keyvault.name",
        "storageAccount.name",
        "adf.name"
    ]

    __fields_validators = {
        "sqlserver.admin.password": common.check_complex_password
    }

    def __init__(self):
        self._wc_admin_ad_group = dict()
        self._wc_employees_ad_group = dict()
        self._wc_service_principal = dict()
        self._watercooler_user = dict()
        self._wc_service_db_user_password = None
        self._jwc_db_user_password = None
        self._m365_reader_service_principal = dict()
        self._jwc_aad_app = dict()
        self._deployment_name = None
        self._required_arm_params = dict()
        self._has_changes = False
        self._arm_params = dict()
        self._adb_cluster_details = dict()
        self._wc_deployer_identity = dict()
        self._log_analytics_workspace_name = None
        self._sql_auth_mode = True
        self._runtime_storage_account_key = None
        InstallConfiguration._load_arm_params(self)

    def get_wc_dir(self):
        return os.path.dirname(self.__dump_file_name)

    @classmethod
    def get_pywc_utils_library_name(self):
        for file in os.listdir(self.__artifacts_path):
            if file.startswith("pywc_utils-"):
                return file

        # if the pyhraph library isn't found using the current file's path
        # we'll try to find it using the convention hardcoded path /wc/scripts/artifacts/
        for file in os.listdir(self.__backup_artifacts_path):
            if file.startswith("pywc_utils-"):
                return file

    @classmethod
    def _load_arm_params(cls, self):
        default_template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mainTemplate.json")
        try:
            if os.path.exists(default_template_path):
                with open(default_template_path, "r") as f:
                    self._arm_params = json.load(f)['parameters']
            else:
                self._arm_params = dict()
        except JSONDecodeError as pe:
            print(pe)
            raise pe

    @property
    def wc_admin_ad_group(self):
        '''
           {
            "ad_group_name": 'displayName',
            "objectId":'objectId'
            }
        :return:
        '''
        return self._wc_admin_ad_group

    @wc_admin_ad_group.setter
    def wc_admin_ad_group(self, value: dict):
        self._wc_admin_ad_group = value
        self._save()

    @property
    def wc_employees_ad_group(self):
        return self._wc_employees_ad_group

    @wc_employees_ad_group.setter
    def wc_employees_ad_group(self, value: dict):
        self._wc_employees_ad_group = value
        self._save()

    @property
    def wc_service_principal(self):
        """
            {"appId": "uuid", "password": "password"}
        :return:
        """
        return self._wc_service_principal

    @wc_service_principal.setter
    def wc_service_principal(self, value: dict):
        self._wc_service_principal = value
        self._save()

    @property
    def watercooler_user(self):
        return self._watercooler_user

    @watercooler_user.setter
    def watercooler_user(self, value: dict):
        self._watercooler_user = value
        self._save()

    @property
    def wc_service_db_user_password(self):
        return self._wc_service_db_user_password

    @wc_service_db_user_password.setter
    def wc_service_db_user_password(self, value: str):
        self._wc_service_db_user_password = value
        self._save()

    @property
    def jwc_db_user_password(self):
        return self._jwc_db_user_password

    @jwc_db_user_password.setter
    def jwc_db_user_password(self, value: str):
        self._jwc_db_user_password = value
        self._save()

    @property
    def m365_reader_service_principal(self):
        return self._m365_reader_service_principal

    @m365_reader_service_principal.setter
    def m365_reader_service_principal(self, value: dict):
        self._m365_reader_service_principal = value
        self._save()

    @property
    def jwc_aad_app(self):
        return self._jwc_aad_app

    @jwc_aad_app.setter
    def jwc_aad_app(self, value: dict):
        self._jwc_aad_app = value
        self._save()

    @property
    def deployment_name(self):
        return self._deployment_name

    @deployment_name.setter
    def deployment_name(self, value: str):
        self._deployment_name = value
        self._save()

    @property
    def required_arm_params(self):
        return dict(self._required_arm_params)

    @property
    def arm_params(self):
        return dict(self._arm_params)

    @property
    def app_keyvault_name(self):
        return self._required_arm_params.get("keyvault.name")

    @property
    def backend_keyvault_name(self):
        return self._required_arm_params.get("m365Adf-keyvault.name")

    @property
    def databricks_workspace_name(self):
        return self._required_arm_params.get("adb.workspace.name")

    @property
    def adb_cluster_details(self):
        return self._adb_cluster_details

    @adb_cluster_details.setter
    def adb_cluster_details(self, value):
        self._adb_cluster_details = value
        self._save()

    @property
    def wc_datafactory_name(self):
        def_param = self._arm_params.get("adf.name") or dict()
        return self._required_arm_params.get("adf.name") or def_param.get("defaultValue")

    @property
    def wc_deployer_identity(self):
        return self._wc_deployer_identity

    @property
    def appservice_name(self):
        def_param = self._arm_params.get("appservice.name") or dict()
        return self._required_arm_params.get("appservice.name") or def_param.get("defaultValue")

    @property
    def appservice_version(self):
        def_param = self._arm_params.get("appservice.version") or dict()
        return self._required_arm_params.get("appservice.version") or def_param.get("defaultValue")

    @wc_deployer_identity.setter
    def wc_deployer_identity(self, value: dict):
        self._wc_deployer_identity = value
        self._save()

    @property
    def log_analytics_workspace_name(self):
        return self._log_analytics_workspace_name

    @log_analytics_workspace_name.setter
    def log_analytics_workspace_name(self, value: str):
        self._log_analytics_workspace_name = value
        self._save()

    @property
    def runtime_storage_account_name(self):
        def_param = self._arm_params.get("storageAccount.name") or dict()
        return self._required_arm_params.get("storageAccount.name") or def_param.get("defaultValue")

    @property
    def runtime_storage_account_key(self):
        return self._runtime_storage_account_key

    @runtime_storage_account_key.setter
    def runtime_storage_account_key(self, value: str):
        self._runtime_storage_account_key = value
        self._save()

    @property
    def sql_auth(self):
        return self._sql_auth_mode

    @sql_auth.setter
    def sql_auth(self, value: bool):
        self._sql_auth_mode = value
        self._save()

    def _save(self):
        if not os.path.exists(self.__dump_file_name):
            if not os.path.exists(os.path.dirname(self.__dump_file_name)):
                os.mkdir(os.path.dirname(self.__dump_file_name), )
        with open(InstallConfiguration.__dump_file_name, "wb") as param_file:
            pickle.dump(self, param_file)

    @classmethod
    def load(cls):
        if path.exists(InstallConfiguration.__dump_file_name):
            with open(InstallConfiguration.__dump_file_name, "rb") as param_file:
                config = pickle.load(param_file)
                InstallConfiguration._load_arm_params(self=config)
                return config
        else:
            return InstallConfiguration()

    def _get_required_arm_params_name(self):
        return list(filter(lambda x: not x.startswith("_") and "metadata" in self._arm_params[x],
                           self._arm_params.keys()))

    def _is_secure_param(self, param_name: str):
        def_param = self._arm_params.get(param_name)
        return def_param and 'type' in def_param and str(def_param['type']).lower() == 'securestring'

    def _get_def_value(self, param_name: str, deployment_name: str):
        param_def = self._arm_params.get(param_name)
        if param_def and "defaultValue" in param_def:
            default_value = param_def["defaultValue"]
            if param_name in self.__unique_properties and deployment_name:
                # see for details https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules
                return default_value + lex_hash(deployment_name)
            else:
                return default_value
        return None

    def _get_parameter_attribute(self, param_name: str, attribute_name: str):
        param_def = self._arm_params.get(param_name)
        if param_def and attribute_name in param_def:
            attribute_value = param_def[attribute_name]
            return attribute_value
        return None

    def _param_description(self, param_name: str):
        def_param = self._arm_params.get(param_name)
        if def_param and "metadata" in def_param:
            return def_param['metadata']['description']

        return None

    def _prompt_param(self, param_name: str, deployment_name: str, is_secure: bool = False, _description: str = None,
                      allow_empty: bool = False):
        description = _description or self._param_description(param_name=param_name)
        def_value = self._get_def_value(param_name=param_name, deployment_name=deployment_name)
        validator_func = self.__fields_validators.get(param_name)
        value = None
        while value is None:
            value = self._required_arm_params.get(param_name) or def_value
            msg = "Enter %s : " % param_name
            if description:
                if is_secure:
                    msg = "Enter %s, %s : " % (param_name, description)
                else:
                    if value:
                        msg = "Enter %s, %s ( default: '%s') : " % (param_name, description, value)
                    else:
                        msg = "Enter %s, %s : " % (param_name, description)
            else:
                msg = "Enter %s : " % param_name

            if is_secure:
                msg = "Enter %s, %s : " % (param_name, description)
                entered_value = getpass.getpass(prompt=msg)
                if validator_func:
                    if not validator_func(entered_value):
                        print("Entered value is invalid, try again")
                        entered_value = None

                if entered_value:
                    confirmed_value = getpass.getpass(prompt="Confirm %s : " % param_name)
                    if entered_value != confirmed_value:
                        entered_value = None
            else:
                entered_value = input(msg)
                if isinstance(def_value, int) and entered_value:
                    entered_value = int(entered_value)
                    # check if the int value is contained in the defined limits, if present
                    min_value = self._get_parameter_attribute(param_name=param_name, attribute_name="minValue")
                    if min_value and entered_value < min_value:
                        entered_value = None
                    max_value = self._get_parameter_attribute(param_name=param_name, attribute_name="maxValue")
                    if max_value and entered_value > max_value:
                        entered_value = None

                if validator_func:
                    if not validator_func(entered_value):
                        entered_value = None

            print("\n")
            if entered_value:
                value = entered_value
            elif allow_empty:
                value = ""

        return value

    def prompt_all_required(self, deployment_name: str):
        param_names = self._get_required_arm_params_name()
        for param_name in sorted(param_names):
            is_secure = self._is_secure_param(param_name=param_name)
            entered_value = self._prompt_param(param_name=param_name, is_secure=is_secure, deployment_name=deployment_name)
            self._required_arm_params[param_name] = entered_value
            self._save()
