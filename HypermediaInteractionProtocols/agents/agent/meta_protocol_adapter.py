import bspl
import logging

logger = logging.getLogger()

RoleNegotiationMetaProtocol = bspl.load_file("RoleNegotiation.bspl").export("RoleNegotiation")

from RoleNegotiation import Initiator, Candidate
from RoleNegotiation import OfferRole, Accept, Reject, SystemDetails
from bspl.adapter import Adapter

adapter = Adapter()

async def offerRole(protocolName, protocolEnactment, proposedRole):
    await adapter.send(
        OfferRole(
            protocolName=protocolName,
            protocolEnactment=protocolEnactment,
            proposedRole=proposedRole
        )
    )

@adapter.reaction(OfferRole)
async def roleDecision(msg):
    """Decide if agent wants to participate in proposed protocolEnactment as proposedRole"""
    logger.info(f"Received Message to play {msg['proposedRole']} in {msg['protocolEnactment']} of protocol {msg['protocolName']}")

    decision = True # arbitrary decision logic
    if decision:
        await adapter.send(
            Accept(
                protocolName=msg['protocolName'],
                protocolEnactment=msg['protocolEnactment'],
                proposedRole=msg['proposedRole'],
                accept=True
            )
        )
    else:
        await adapter.send(
            Reject(
                protocolName=msg['protocolName'],
                protocolEnactment=msg['protocolEnactment'],
                proposedRole=msg['proposedRole'],
                reject=True
            )
        )

@adapter.enabled(SystemDetails)
async def shareProtocolInformation(msg):
    """At this point we know all roles and can send out the system details"""
    await adapter.send(
        SystemDetails(
            
        )
    )

