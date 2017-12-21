from network_manager import NetworkManager
from core.enums import numericEnum
from core.decision import Decision
import types


class ServerNetworkManager (NetworkManager):
    def __init__(self, base):
        super().__init__()
        self.base = base

    Opcodes = numericEnum(
        'addPlayer',
        'selectFaction',
        'revealFacedown',
        'playFaceup',
        'attack',
        'play',
        'acceptTarget',
        'endPhase')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode, ", self.Opcodes.keys[opcode])
        try:
            getattr(self.base, self.Opcodes.keys[opcode])(addr, *operands)
        except Decision as d:
            d.addr = addr
            raise d


class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into
    calls to the client.
    """
    def __init__(self, base, ip, port):
        super().__init__()
        self.base = base
        self.ip = ip
        self.port = port

        # Make it so each server opcode is a function
        for i, key in enumerate(ServerNetworkManager.Opcodes.keys):
            class OpcodeFunc:
                def __init__(self, opcode):
                    self.opcode = opcode

                def __call__(self, base, *args):
                    base.sendInts(
                        (base.ip, base.port),
                        self.opcode,
                        *args)

            # Bind the OpcodeFunc as a method to the class
            setattr(self, key, types.MethodType(OpcodeFunc(i), self))

    Opcodes = numericEnum(
        'updateEnemyFaction',
        'updatePlayerHand',
        'updateEnemyHand',
        'updatePlayerFacedowns',
        'updateEnemyFacedowns',
        'updatePlayerFaceups',
        'updateEnemyFaceups',
        'updatePlayerManaCap',
        'updatePlayerMana',
        'updateEnemyManaCap',
        'updatePhase',
        'requestTarget',
        'winGame',
        'loseGame',
        'setActive')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode, ", self.Opcodes.keys[opcode])
        getattr(self.base, self.Opcodes.keys[opcode])(*operands)
