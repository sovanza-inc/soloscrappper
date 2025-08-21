import os
import hashlib
import uuid
import platform
import pickle
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("psycopg2 is not installed. Please install it using:")
    print("pip install psycopg2-binary")
    raise ImportError("psycopg2 is required for license management")


class LicenseManager:
    """Manages license validation with Neon database"""
    
    def __init__(self):
        self.connection_string = "postgresql://neondb_owner:npg_4GvhMte9BIoW@ep-mute-waterfall-ad00hkay-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        self.machine_id = self._generate_machine_id()
        self.cache_file = os.path.join(os.path.expanduser("~"), ".solo_scrapper_license.cache")
    
    def _generate_machine_id(self) -> str:
        """Generate unique machine ID based on hardware characteristics"""
        try:
            # Get system information
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'node': platform.node()
            }
            
            # Create a unique string from system info
            info_string = ''.join(str(v) for v in system_info.values())
            
            # Generate hash
            machine_hash = hashlib.sha256(info_string.encode()).hexdigest()[:16]
            return machine_hash
        except Exception:
            # Fallback to UUID if system info fails
            return str(uuid.uuid4())[:16]
    
    def _get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.connection_string)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def validate_license(self, license_key: str) -> Tuple[bool, str]:
        """Validate license key against database"""
        if not license_key or len(license_key.strip()) == 0:
            return False, "License key cannot be empty"
        
        conn = self._get_connection()
        if not conn:
            return False, "Unable to connect to license server"
        
        try:
            cursor = conn.cursor()
            
            # Check if license exists and is valid
            cursor.execute(
                "SELECT machine_id, valid, expires_at FROM licenses WHERE key = %s",
                (license_key,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                return False, "Invalid license key"
            
            machine_id, valid, expires_at = result
            
            if not valid:
                return False, "License key has been deactivated"
            
            if expires_at and expires_at < datetime.now():
                return False, "License key has expired"
            
            # Check if license is already bound to another machine
            if machine_id and machine_id != self.machine_id:
                return False, "License key is already bound to another machine"
            
            # Bind license to this machine if not already bound
            if not machine_id:
                cursor.execute(
                    "UPDATE licenses SET machine_id = %s WHERE key = %s",
                    (self.machine_id, license_key)
                )
                conn.commit()
            
            # Save to local cache for future use
            self._save_license_cache(license_key, expires_at)
            
            return True, "License validated successfully"
            
        except Exception as e:
            return False, f"License validation error: {str(e)}"
        finally:
            conn.close()
    
    def get_machine_id(self) -> str:
        """Get the current machine ID"""
        return self.machine_id
    
    def _save_license_cache(self, license_key: str, expires_at: datetime = None):
        """Save validated license to local cache"""
        try:
            cache_data = {
                'license_key': license_key,
                'machine_id': self.machine_id,
                'validated_at': datetime.now(),
                'expires_at': expires_at,
                'version': '1.0'
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"Failed to save license cache: {e}")
    
    def _load_license_cache(self) -> Optional[Dict]:
        """Load license cache from local file"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verify cache is for this machine
            if cache_data.get('machine_id') != self.machine_id:
                return None
            
            # Check if cache has expired (cache valid for 7 days)
            validated_at = cache_data.get('validated_at')
            if validated_at and (datetime.now() - validated_at).days > 7:
                return None
            
            # Check if license itself has expired
            expires_at = cache_data.get('expires_at')
            if expires_at and expires_at < datetime.now():
                return None
            
            return cache_data
        except Exception as e:
            print(f"Failed to load license cache: {e}")
            return None
    
    def verify_cached_license_with_database(self, license_key: str) -> bool:
        """Verify cached license against database to detect changes/revocations"""
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute(
                "SELECT machine_id, expires_at, valid FROM licenses WHERE key = %s",
                (license_key,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                # License doesn't exist in database anymore
                return False
            
            machine_id, expires_at, valid = result
            
            # Check if license is still valid
            if not valid:
                return False
            
            # Check if license is still bound to this machine
            if machine_id and machine_id != self.machine_id:
                return False
            
            # Check if license hasn't expired
            if expires_at and datetime.now() > expires_at:
                return False
            
            return True
            
        except Exception as e:
            print(f"Failed to verify cached license with database: {e}")
            return False
    
    def has_valid_cached_license(self) -> bool:
        """Check if there's a valid cached license"""
        cache_data = self._load_license_cache()
        if not cache_data:
            return False
        
        # Periodically verify with database (every 24 hours)
        validated_at = cache_data.get('validated_at')
        if validated_at and (datetime.now() - validated_at).total_seconds() >= 24 * 3600:
            license_key = cache_data.get('license_key')
            if license_key and not self.verify_cached_license_with_database(license_key):
                self.clear_license_cache()
                return False
        
        return True
    
    def get_cached_license_key(self) -> Optional[str]:
        """Get the cached license key if valid"""
        cache_data = self._load_license_cache()
        return cache_data.get('license_key') if cache_data else None
    
    def clear_license_cache(self):
        """Clear the license cache"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
        except Exception as e:
            print(f"Failed to clear license cache: {e}")
    
    def get_license_status(self) -> Dict[str, str]:
        """Get current license status information"""
        try:
            if self.has_valid_cached_license():
                cache_data = self._load_license_cache()
                if cache_data:
                    expires_at = cache_data.get('expires_at')
                    if expires_at:
                        if isinstance(expires_at, str):
                            expires_at = datetime.fromisoformat(expires_at)
                        days_left = (expires_at - datetime.now()).days
                        if days_left > 30:
                            return {
                                'status': 'active',
                                'message': f"✅ License Active ({days_left} days left)",
                                'type': 'success'
                            }
                        elif days_left > 0:
                            return {
                                'status': 'expiring',
                                'message': f"⚠️ License Expires Soon ({days_left} days)",
                                'type': 'warning'
                            }
                        else:
                            return {
                                'status': 'expired',
                                'message': "❌ License Expired",
                                'type': 'error'
                            }
                    else:
                        return {
                            'status': 'active',
                            'message': "✅ License Active (Permanent)",
                            'type': 'success'
                        }
                else:
                    return {
                        'status': 'active',
                        'message': "✅ License Active",
                        'type': 'success'
                    }
            else:
                # Check database connection
                conn = self._get_connection()
                if conn:
                    conn.close()
                    return {
                        'status': 'inactive',
                        'message': "🔑 No License - Click to Activate",
                        'type': 'inactive'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': "❌ Database Connection Failed",
                        'type': 'error'
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': "❌ License System Error",
                'type': 'error'
            }
    
    def get_detailed_license_info(self) -> Dict[str, str]:
        """Get detailed license information for display"""
        try:
            info = {
                'has_license': False,
                'license_key': 'Not activated',
                'status': 'Inactive',
                'expires_at': 'N/A',
                'days_remaining': 'N/A',
                'machine_id': self.get_machine_id(),
                'is_bound': False
            }
            
            if self.has_valid_cached_license():
                cached_key = self.get_cached_license_key()
                cache_data = self._load_license_cache()
                
                info['has_license'] = True
                info['license_key'] = cached_key[:8] + '...' + cached_key[-4:] if len(cached_key) > 12 else cached_key
                info['is_bound'] = True
                
                if cache_data and 'expires_at' in cache_data:
                    expires_at = cache_data['expires_at']
                    if expires_at:
                        if isinstance(expires_at, str):
                            expires_at = datetime.fromisoformat(expires_at)
                        info['expires_at'] = expires_at.strftime('%Y-%m-%d %H:%M:%S')
                        days_left = (expires_at - datetime.now()).days
                        info['days_remaining'] = max(0, days_left)
                        
                        if days_left > 0:
                            info['status'] = 'Active'
                        else:
                            info['status'] = 'Expired'
                    else:
                        info['expires_at'] = 'Permanent'
                        info['days_remaining'] = '∞'
                        info['status'] = 'Active (Permanent)'
                else:
                    info['status'] = 'Active'
            
            return info
        except Exception as e:
            return {
                'has_license': False,
                'license_key': 'Error',
                'status': f'Error: {str(e)}',
                'expires_at': 'N/A',
                'days_remaining': 'N/A',
                'machine_id': 'Unknown',
                'is_bound': False
            }
    
    def unbind_license(self, license_key: str) -> Tuple[bool, str]:
        """Unbind license from current machine"""
        try:
            conn = self._get_connection()
            if not conn:
                return False, "Unable to connect to license server"
            
            cursor = conn.cursor()
            
            # Check if license exists and is bound to this machine
            cursor.execute(
                "SELECT machine_id FROM licenses WHERE key = %s",
                (license_key,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                return False, "License key not found"
            
            machine_id = result[0]
            
            if machine_id != self.machine_id:
                return False, "License is not bound to this machine"
            
            # Unbind the license
            cursor.execute(
                "UPDATE licenses SET machine_id = NULL WHERE key = %s",
                (license_key,)
            )
            
            conn.commit()
            conn.close()
            
            # Clear local cache
            self.clear_license_cache()
            
            return True, "License unbound successfully"
            
        except Exception as e:
            return False, f"Error unbinding license: {str(e)}"