#=========================================================================
# [AutoDelete - Telegram bot to delete messages after specific time]      
# Copyright (C) 2022 Arunkumar Shibu                       
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#=========================================================================

# Remove the wildcard import from delete.py
from .info import Config
from .database import (
    save_message,
    get_all_data,
    delete_all_data,
    save_group_settings,
    get_group_settings,
    get_all_authorized_groups,
    get_group_deletion_time
)

# Explicitly export what you need
__all__ = [
    'Config',
    'save_message',
    'get_all_data',
    'delete_all_data',
    'save_group_settings',
    'get_group_settings',
    'get_all_authorized_groups',
    'get_group_deletion_time'
]