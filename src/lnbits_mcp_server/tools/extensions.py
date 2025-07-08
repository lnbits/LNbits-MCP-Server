"""Extension-specific tools for LNbits MCP server."""

from typing import Any, Dict, List, Optional

import structlog

from ..client import LNbitsClient, LNbitsError

logger = structlog.get_logger(__name__)


class ExtensionTools:
    """Tools for LNbits extensions."""
    
    def __init__(self, client: LNbitsClient):
        self.client = client
        
    # LNURLp (Pay) Extension
    async def create_lnurlp_link(
        self,
        description: str,
        amount: int,
        comment_chars: int = 200,
        success_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an LNURLp pay link."""
        try:
        
            data = {
                "description": description,
                "amount": amount,
                "comment_chars": comment_chars,
                "success_text": success_text or "Payment successful!",
            }
            
            response = await self.client.post("/lnurlp/api/v1/links", json=data)
            
            link_info = {
                "id": response.get("id"),
                "lnurl": response.get("lnurl"),
                "description": description,
                "amount": amount,
                "comment_chars": comment_chars,
                "success_text": success_text,
                "served_meta": response.get("served_meta", 0),
                "served_pr": response.get("served_pr", 0),
                "webhook_url": response.get("webhook_url"),
            }
            
            logger.info("Created LNURLp link", id=link_info["id"], amount=amount)
            return link_info
            
        except LNbitsError as e:
        logger.error("Failed to create LNURLp link", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error creating LNURLp link", error=str(e))
        raise LNbitsError(f"Failed to create LNURLp link: {str(e)}")
    
    async def get_lnurlp_links(self) -> List[Dict[str, Any]]:
        """Get all LNURLp pay links."""
        try:
        
            response = await self.client.get("/lnurlp/api/v1/links")
            
            links = []
            for link_data in response:
                link = {
                    "id": link_data.get("id"),
                    "lnurl": link_data.get("lnurl"),
                    "description": link_data.get("description"),
                    "amount": link_data.get("amount"),
                    "served_meta": link_data.get("served_meta", 0),
                    "served_pr": link_data.get("served_pr", 0),
                    "webhook_url": link_data.get("webhook_url"),
                }
                links.append(link)
            
            logger.info("Retrieved LNURLp links", count=len(links))
            return links
            
        except LNbitsError as e:
        logger.error("Failed to get LNURLp links", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting LNURLp links", error=str(e))
        raise LNbitsError(f"Failed to get LNURLp links: {str(e)}")
    
    # TPoS (Terminal Point of Sale) Extension
    async def create_tpos(
        self,
        name: str,
        currency: str = "USD",
        tip_options: Optional[List[int]] = None,
        tip_wallet: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a TPoS terminal."""
        try:
        
            data = {
                "name": name,
                "currency": currency,
                "tip_options": tip_options or [5, 10, 15, 20],
            }
            if tip_wallet:
                data["tip_wallet"] = tip_wallet
            
            response = await self.client.post("/tpos/api/v1/tposs", json=data)
            
            tpos_info = {
                "id": response.get("id"),
                "name": name,
                "wallet": response.get("wallet"),
                "currency": currency,
                "tip_options": tip_options,
                "tip_wallet": tip_wallet,
            }
            
            logger.info("Created TPoS", id=tpos_info["id"], name=name)
            return tpos_info
            
        except LNbitsError as e:
        logger.error("Failed to create TPoS", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error creating TPoS", error=str(e))
        raise LNbitsError(f"Failed to create TPoS: {str(e)}")
    
    async def get_tpos_list(self) -> List[Dict[str, Any]]:
        """Get all TPoS terminals."""
        try:
        
            response = await self.client.get("/tpos/api/v1/tposs")
            
            terminals = []
            for tpos_data in response:
                terminal = {
                    "id": tpos_data.get("id"),
                    "name": tpos_data.get("name"),
                    "wallet": tpos_data.get("wallet"),
                    "currency": tpos_data.get("currency"),
                    "tip_options": tpos_data.get("tip_options"),
                    "tip_wallet": tpos_data.get("tip_wallet"),
                }
                terminals.append(terminal)
            
            logger.info("Retrieved TPoS list", count=len(terminals))
            return terminals
            
        except LNbitsError as e:
        logger.error("Failed to get TPoS list", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting TPoS list", error=str(e))
        raise LNbitsError(f"Failed to get TPoS list: {str(e)}")
    
    # SatsPay Extension
    async def create_satspay_charge(
        self,
        amount: int,
        description: str,
        webhook: Optional[str] = None,
        completelink: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a SatsPay charge."""
        try:
        
            data = {
                "amount": amount,
                "description": description,
            }
            if webhook:
                data["webhook"] = webhook
            if completelink:
                data["completelink"] = completelink
            
            response = await self.client.post("/satspay/api/v1/charges", json=data)
            
            charge_info = {
                "id": response.get("id"),
                "amount": amount,
                "description": description,
                "webhook": webhook,
                "completelink": completelink,
                "bolt11": response.get("bolt11"),
                "payment_hash": response.get("payment_hash"),
                "status": response.get("status", "pending"),
                "paid": response.get("paid", False),
            }
            
            logger.info("Created SatsPay charge", id=charge_info["id"], amount=amount)
            return charge_info
            
        except LNbitsError as e:
        logger.error("Failed to create SatsPay charge", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error creating SatsPay charge", error=str(e))
        raise LNbitsError(f"Failed to create SatsPay charge: {str(e)}")
    
    async def get_satspay_charges(self) -> List[Dict[str, Any]]:
        """Get all SatsPay charges."""
        try:
        
            response = await self.client.get("/satspay/api/v1/charges")
            
            charges = []
            for charge_data in response:
                charge = {
                    "id": charge_data.get("id"),
                    "amount": charge_data.get("amount"),
                    "description": charge_data.get("description"),
                    "bolt11": charge_data.get("bolt11"),
                    "payment_hash": charge_data.get("payment_hash"),
                    "status": charge_data.get("status"),
                    "paid": charge_data.get("paid", False),
                    "time": charge_data.get("time"),
                }
                charges.append(charge)
            
            logger.info("Retrieved SatsPay charges", count=len(charges))
            return charges
            
        except LNbitsError as e:
        logger.error("Failed to get SatsPay charges", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting SatsPay charges", error=str(e))
        raise LNbitsError(f"Failed to get SatsPay charges: {str(e)}")
    
    # Watch-only Extension
    async def create_watchonly_wallet(
        self,
        title: str,
        address: str,
        network: str = "Mainnet",
    ) -> Dict[str, Any]:
        """Create a watch-only wallet."""
        try:
        
            data = {
                "title": title,
                "address": address,
                "network": network,
            }
            
            response = await self.client.post("/watchonly/api/v1/wallet", json=data)
            
            wallet_info = {
                "id": response.get("id"),
                "title": title,
                "address": address,
                "network": network,
                "balance": response.get("balance", 0),
                "type": response.get("type"),
            }
            
            logger.info("Created watch-only wallet", id=wallet_info["id"], title=title)
            return wallet_info
            
        except LNbitsError as e:
        logger.error("Failed to create watch-only wallet", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error creating watch-only wallet", error=str(e))
        raise LNbitsError(f"Failed to create watch-only wallet: {str(e)}")
    
    async def get_watchonly_wallets(self, network: str = "Mainnet") -> List[Dict[str, Any]]:
        """Get all watch-only wallets."""
        try:
        
            params = {"network": network}
            response = await self.client.get("/watchonly/api/v1/wallet", params=params)
            
            wallets = []
            for wallet_data in response:
                wallet = {
                    "id": wallet_data.get("id"),
                    "title": wallet_data.get("title"),
                    "address": wallet_data.get("address"),
                    "balance": wallet_data.get("balance", 0),
                    "type": wallet_data.get("type"),
                    "network": network,
                }
                wallets.append(wallet)
            
            logger.info("Retrieved watch-only wallets", count=len(wallets))
            return wallets
            
        except LNbitsError as e:
        logger.error("Failed to get watch-only wallets", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error getting watch-only wallets", error=str(e))
        raise LNbitsError(f"Failed to get watch-only wallets: {str(e)}")
    
    # Extension Management
    async def list_available_extensions(self) -> List[Dict[str, Any]]:
        """List all available extensions."""
        try:
        
            response = await self.client.get("/api/v1/extensions")
            
            extensions = []
            for ext_data in response:
                extension = {
                    "id": ext_data.get("id"),
                    "name": ext_data.get("name"),
                    "short_description": ext_data.get("short_description"),
                    "icon": ext_data.get("icon"),
                    "contributors": ext_data.get("contributors", []),
                    "installed": ext_data.get("installed", False),
                    "activated": ext_data.get("activated", False),
                    "is_admin_only": ext_data.get("is_admin_only", False),
                }
                extensions.append(extension)
            
            logger.info("Retrieved available extensions", count=len(extensions))
            return extensions
            
        except LNbitsError as e:
        logger.error("Failed to list extensions", error=str(e))
        raise
        except Exception as e:
        logger.error("Unexpected error listing extensions", error=str(e))
        raise LNbitsError(f"Failed to list extensions: {str(e)}")
    
    async def get_extension_status(self, extension_id: str) -> Dict[str, Any]:
        """Get status of a specific extension."""
        try:
        
            response = await self.client.get(f"/api/v1/extensions/{extension_id}")
            
            status = {
                "id": extension_id,
                "name": response.get("name"),
                "installed": response.get("installed", False),
                "activated": response.get("activated", False),
                "version": response.get("version"),
                "is_admin_only": response.get("is_admin_only", False),
                "config": response.get("config", {}),
            }
            
            logger.info("Retrieved extension status", extension_id=extension_id, installed=status["installed"])
            return status
            
        except LNbitsError as e:
        logger.error("Failed to get extension status", error=str(e), extension_id=extension_id)
        raise
        except Exception as e:
        logger.error("Unexpected error getting extension status", error=str(e), extension_id=extension_id)
        raise LNbitsError(f"Failed to get extension status: {str(e)}")