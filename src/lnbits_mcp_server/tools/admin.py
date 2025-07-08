"""Admin tools for LNbits MCP server."""

from typing import Any, Dict, List, Optional

import structlog

from ..client import LNbitsClient, LNbitsError

logger = structlog.get_logger(__name__)


class AdminTools:
    """Administrative tools for LNbits."""
    
    def __init__(self, client: LNbitsClient):
        self.client = client
        
    async def get_node_info(self) -> Dict[str, Any]:
        """Get Lightning node information."""
        try:
        
            response = await self.client.get("/api/v1/node")
            
            node_info = {
                "alias": response.get("alias"),
                "public_key": response.get("id"),
                "version": response.get("version"),
                "num_peers": response.get("num_peers", 0),
                "num_active_channels": response.get("num_active_channels", 0),
                "num_inactive_channels": response.get("num_inactive_channels", 0),
                "num_pending_channels": response.get("num_pending_channels", 0),
                "block_height": response.get("block_height", 0),
                "synced_to_chain": response.get("synced_to_chain", False),
                "synced_to_graph": response.get("synced_to_graph", False),
                "testnet": response.get("testnet", False),
                "uris": response.get("uris", []),
                "features": response.get("features", {}),
            }
            
            logger.info("Retrieved node info", alias=node_info["alias"], public_key=node_info["public_key"])
            return node_info
            
        except LNbitsError as e:
        logger.error("Failed to get node info", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting node info", error=str(e))
        raise LNbitsError(f"Failed to get node info: {str(e)}")
    
    async def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        try:
        
            response = await self.client.get("/usermanager/api/v1/users")
            
            users = []
            for user_data in response:
                user = {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "username": user_data.get("username"),
                    "admin": user_data.get("admin", False),
                    "super_user": user_data.get("super_user", False),
                    "created_at": user_data.get("created_at"),
                    "last_login": user_data.get("last_login"),
                    "extensions": user_data.get("extensions", []),
                    "wallets": user_data.get("wallets", []),
                }
                users.append(user)
            
            logger.info("Retrieved users list", count=len(users))
            return users
            
        except LNbitsError as e:
        logger.error("Failed to list users", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error listing users", error=str(e))
        raise LNbitsError(f"Failed to list users: {str(e)}")
    
    async def create_user(
        self,
        email: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        admin: bool = False,
    ) -> Dict[str, Any]:
        """Create a new user."""
        try:
        
            data = {
                "email": email,
                "admin": admin,
            }
            if username:
                data["username"] = username
            if password:
                data["password"] = password
            
            response = await self.client.post("/usermanager/api/v1/users", json=data)
            
            user_info = {
                "id": response.get("id"),
                "email": email,
                "username": username,
                "admin": admin,
                "created_at": response.get("created_at"),
                "wallet_id": response.get("wallet_id"),
            }
            
            logger.info("Created user", user_id=user_info["id"], email=email)
            return user_info
            
        except LNbitsError as e:
        logger.error("Failed to create user", error=str(e), email=email)
        raise
        except Exception as e:
        logger.error("Unexpected error creating user", error=str(e), email=email)
        raise LNbitsError(f"Failed to create user: {str(e)}")
    
    async def get_user_details(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a user."""
        try:
        
            response = await self.client.get(f"/usermanager/api/v1/users/{user_id}")
            
            user_details = {
                "id": user_id,
                "email": response.get("email"),
                "username": response.get("username"),
                "admin": response.get("admin", False),
                "super_user": response.get("super_user", False),
                "created_at": response.get("created_at"),
                "last_login": response.get("last_login"),
                "extensions": response.get("extensions", []),
                "wallets": response.get("wallets", []),
                "balance": response.get("balance", 0),
            }
            
            logger.info("Retrieved user details", user_id=user_id, email=user_details["email"])
            return user_details
            
        except LNbitsError as e:
        logger.error("Failed to get user details", error=str(e), user_id=user_id)
        raise
        except Exception as e:
        logger.error("Unexpected error getting user details", error=str(e), user_id=user_id)
        raise LNbitsError(f"Failed to get user details: {str(e)}")
    
    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user."""
        try:
        
            await self.client.delete(f"/usermanager/api/v1/users/{user_id}")
            
            result = {
                "user_id": user_id,
                "deleted": True,
                "message": "User deleted successfully",
            }
            
            logger.info("Deleted user", user_id=user_id)
            return result
            
        except LNbitsError as e:
        logger.error("Failed to delete user", error=str(e), user_id=user_id)
        raise
        except Exception as e:
        logger.error("Unexpected error deleting user", error=str(e), user_id=user_id)
        raise LNbitsError(f"Failed to delete user: {str(e)}")
    
    async def list_wallets(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all wallets or wallets for a specific user."""
        try:
        
            if user_id:
                response = await self.client.get(f"/api/v1/wallets/{user_id}")
            else:
                response = await self.client.get("/api/v1/wallets")
            
            wallets = []
            for wallet_data in response:
                wallet = {
                    "id": wallet_data.get("id"),
                    "name": wallet_data.get("name"),
                    "user": wallet_data.get("user"),
                    "balance": wallet_data.get("balance", 0),
                    "adminkey": bool(wallet_data.get("adminkey")),
                    "inkey": bool(wallet_data.get("inkey")),
                    "created_at": wallet_data.get("created_at"),
                }
                wallets.append(wallet)
            
            logger.info("Retrieved wallets", count=len(wallets), user_id=user_id)
            return wallets
            
        except LNbitsError as e:
        logger.error("Failed to list wallets", error=str(e), user_id=user_id)
        raise
        except Exception as e:
        logger.error("Unexpected error listing wallets", error=str(e), user_id=user_id)
        raise LNbitsError(f"Failed to list wallets: {str(e)}")
    
    async def create_wallet(
        self,
        user_id: str,
        wallet_name: str,
        admin_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new wallet for a user."""
        try:
        
            data = {
                "user_id": user_id,
                "wallet_name": wallet_name,
            }
            if admin_key:
                data["admin_key"] = admin_key
            
            response = await self.client.post("/api/v1/wallets", json=data)
            
            wallet_info = {
                "id": response.get("id"),
                "name": wallet_name,
                "user": user_id,
                "adminkey": response.get("adminkey"),
                "inkey": response.get("inkey"),
                "balance": 0,
                "created_at": response.get("created_at"),
            }
            
            logger.info("Created wallet", wallet_id=wallet_info["id"], name=wallet_name, user_id=user_id)
            return wallet_info
            
        except LNbitsError as e:
        logger.error("Failed to create wallet", error=str(e), user_id=user_id)
        raise
        except Exception as e:
        logger.error("Unexpected error creating wallet", error=str(e), user_id=user_id)
        raise LNbitsError(f"Failed to create wallet: {str(e)}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
        
            response = await self.client.get("/api/v1/audit")
            
            stats = {
                "total_users": response.get("total_users", 0),
                "total_wallets": response.get("total_wallets", 0),
                "total_payments": response.get("total_payments", 0),
                "total_invoices": response.get("total_invoices", 0),
                "total_volume": response.get("total_volume", 0),
                "total_fees": response.get("total_fees", 0),
                "node_balance": response.get("node_balance", 0),
                "channels_balance": response.get("channels_balance", 0),
                "pending_payments": response.get("pending_payments", 0),
                "failed_payments": response.get("failed_payments", 0),
                "successful_payments": response.get("successful_payments", 0),
            }
            
            logger.info("Retrieved system stats", total_users=stats["total_users"])
            return stats
            
        except LNbitsError as e:
        logger.error("Failed to get system stats", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting system stats", error=str(e))
        raise LNbitsError(f"Failed to get system stats: {str(e)}")
    
    async def backup_database(self) -> Dict[str, Any]:
        """Create a database backup."""
        try:
        
            response = await self.client.post("/api/v1/admin/backup")
            
            backup_info = {
                "backup_id": response.get("backup_id"),
                "created_at": response.get("created_at"),
                "size": response.get("size"),
                "filename": response.get("filename"),
                "download_url": response.get("download_url"),
            }
            
            logger.info("Created database backup", backup_id=backup_info["backup_id"])
            return backup_info
            
        except LNbitsError as e:
        logger.error("Failed to create backup", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error creating backup", error=str(e))
        raise LNbitsError(f"Failed to create backup: {str(e)}")
    
    async def get_logs(
        self,
        limit: int = 100,
        level: str = "INFO",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get system logs."""
        try:
        
            params = {"limit": limit, "level": level}
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            
            response = await self.client.get("/api/v1/admin/logs", params=params)
            
            logs = []
            for log_entry in response:
                log = {
                    "timestamp": log_entry.get("timestamp"),
                    "level": log_entry.get("level"),
                    "message": log_entry.get("message"),
                    "module": log_entry.get("module"),
                    "user_id": log_entry.get("user_id"),
                    "wallet_id": log_entry.get("wallet_id"),
                    "metadata": log_entry.get("metadata", {}),
                }
                logs.append(log)
            
            logger.info("Retrieved logs", count=len(logs), level=level)
            return logs
            
        except LNbitsError as e:
        logger.error("Failed to get logs", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting logs", error=str(e))
        raise LNbitsError(f"Failed to get logs: {str(e)}")