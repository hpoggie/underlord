"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText

from network import ClientNetworkManager, ServerNetworkManager
from server import Zone
from core.enums import Phase

from panda3d.core import loadPrcFileData
from direct.task import Task
from factions import templars

import sys
from fanHand import fanHand
from mouse import MouseHandler
from connectionUI import ConnectionUI

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """)


class IllegalMoveError (Exception):
    pass


class App (ShowBase):
    def __init__(self, argv):
        ShowBase.__init__(self)

        self.port = 9099

        self.scene = self.render.attachNewNode('empty')
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.taskMgr.add(self.mouseOverTask, "MouseOverTask")

        self._active = False
        self._started = False

        # Connect to the default server if no argument provided
        ip = argv[1] if len(argv) > 1 else "174.138.119.84"
        self.connectionUI = ConnectionUI(ip)

    def connect(self, ip):
        self.serverIp = ip
        self.networkManager = ClientNetworkManager(self, self.serverIp)
        self.serverAddr = (self.serverIp, self.port)
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")
        self.networkManager.connect(self.serverAddr)
        self.networkManager.send("0", self.serverAddr)

    def loadModel(self, name):
        ret = self.loader.loadModel(name + ".bam")
        return ret

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        if not self._started:
            self.startGame()
            self._started = True

    def makeFactionSelectUI(self):
        self.factionSelectLabel = OnscreenText(
            text="faction select",
            pos=(0, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.availableFactions = [templars.Templars]

        self.factionButtons = []

        for i, faction in enumerate(self.availableFactions):
            self.factionButtons.append(DirectButton(
                image=faction.iconPath + '/' + faction.cardBack,
                pos=(i * 0.2, 0, 0),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=self.pickFaction,
                extraArgs=[i]))

    def pickFaction(self, index):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.selectFaction,
            index)

        self.faction = self.availableFactions[index]

        self.factionSelectLabel.detachNode()

    def startGame(self):
        self.player = self.faction.player(self.faction)
        self.enemy = self.enemyFaction.player(self.enemyFaction)
        self.phase = Phase.reveal

        self.playerIconPath = self.faction.iconPath
        self.enemyIconPath = self.enemyFaction.iconPath
        self.playerCardBack = self.faction.cardBack
        self.enemyCardBack = self.enemyFaction.cardBack
        self.makeGameUi()

        for button in self.factionButtons:
            button.destroy()
        del self.factionButtons

    def makeGameUi(self):
        self.turnLabel = OnscreenText(
            text="",
            pos=(0, -0.9, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.playerManaCapLabel = OnscreenText(
            text=str(self.player.manaCap),
            pos=(-0.4, -0.44, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.enemyManaCapLabel = OnscreenText(
            text=str(self.enemy.manaCap),
            pos=(-0.5, 0.77),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.cardNameLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = OnscreenText(
            text="",
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = OnscreenText(
            text="",
            pos=(0.7, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.endPhaseButton = DirectButton(
            image="./end_phase.png",
            pos=(0.7, 0, -0.85),
            scale=(0.1, 0.1, 0.1),
            relief=None,
            command=self.endPhase)

        self.playerHandNodes = []
        self.enemyHandNodes = []
        self.playerFacedownNodes = []
        self.enemyFacedownNodes = []
        self.playerFaceupNodes = []
        self.enemyFaceupNodes = []

        self.makePlayerHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

    def updateEnemyFaction(self, index):
        self.enemyFaction = self.availableFactions[index]

    def updatePlayerHand(self, *cardIds):
        self.player.hand = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.hand[i] = self.faction.deck[x]
            self.player.hand[i].owner = self.player
        self.redraw()

    def updateEnemyHand(self, size):
        self.enemy.hand = [None] * size

    def updatePlayerFacedowns(self, *cardIds):
        self.player.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.facedowns[i] = self.faction.deck[x]
            self.player.facedowns[i].owner = self.player
        self.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        self.enemy.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            card = self.enemyFaction.deck[x]
            self.enemy.facedowns[i] = card if x != -1 else None
            if x != -1:
                self.enemy.facedowns[i].owner = self.enemy
        self.redraw()

    def updatePlayerFaceups(self, *cardIds):
        self.player.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.faceups[i] = self.faction.deck[x]
            self.player.faceups[i].owner = self.player
        self.redraw()

    def updateEnemyFaceups(self, *cardIds):
        self.enemy.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.enemy.faceups[i] = self.enemyFaction.deck[x]
            self.enemy.faceups[i].owner = self.enemy
        self.redraw()

    def updatePlayerManaCap(self, manaCap):
        self.player.manaCap = manaCap
        self.redraw()

    def updatePlayerMana(self, mana):
        self.player.mana = mana
        self.redraw()

    def updateEnemyManaCap(self, manaCap):
        self.enemy.manaCap = manaCap
        self.redraw()

    def updatePhase(self, phase):
        self.phase = phase

    def setActive(self, value):
        self.active = bool(value)

    def winGame(self):
        self.winLabel = OnscreenText(
            text="Victory",
            scale=(0.5, 0.5, 0.5))

    def loseGame(self):
        self.winLabel = OnscreenText(
            text="Defeat",
            scale=(0.5, 0.5, 0.5))

    def requestTarget(self):
        self.mouseHandler.targeting = True

    def acceptTarget(self, target):
        targetsEnemy = True
        targetIndex = -1
        targetZone = -1
        if target.getTag('zone') == 'face-down':
            try:
                targetIndex = self.playerFacedownNodes.index(target)
                targetZone = Zone.facedown
                targetsEnemy = False
            except ValueError as e:
                print(e)
        if target.getTag('zone') == 'enemy face-down':
            try:
                targetIndex = self.enemyFacedownNodes.index(target)
                targetZone = Zone.facedown
            except ValueError as e:
                print(e)
        elif target.getTag('zone') == 'face-up':
            try:
                targetIndex = self.enemyFaceupNodes.index(target)
                targetZone = Zone.faceup
            except ValueError as e:
                print(e)
        elif target.getTag('zone') == 'hand':
            try:
                targetIndex = self.playerHandNodes.index(target)
                targetZone = Zone.hand
                targetsEnemy = False
            except ValueError as e:
                print(e)

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.acceptTarget,
            int(targetsEnemy),
            targetZone,
            targetIndex)

    def makePlayerHand(self):
        """
        Redraw the player's hand.
        """
        # Destroy entire hand. This is slow and may need to be changed
        for i in self.playerHandNodes:
            i.detachNode()

        self.playerHandNodes = []

        if not hasattr(self, 'playerHand'):
            self.playerHand = self.scene.attachNewNode('playerHand')

        def addHandCard(card, tr):
            cardModel = self.loadCard(card)
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setTag('zone', 'hand')
            self.playerHandNodes.append(cardModel)
            pivot.reparentTo(self.playerHand)

        fan = fanHand(len(self.player.hand))
        for i, tr in enumerate(fan):
            addHandCard(self.player.hand[i], tr)

        self.playerHand.setPosHpr(2.5, -1.0, 0, 0, 45.0, 0)

    def makeEnemyHand(self):
        for i in self.enemyHandNodes:
            i.detachNode()

        self.enemyHandNodes = []

        if not hasattr(self, 'enemyHand'):
            self.enemyHand = self.scene.attachNewNode('enemyHand')

        def addEnemyHandCard(tr):
            cardModel = self.loadEnemyBlank()
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setTag('zone', 'enemy hand')
            self.enemyHandNodes.append(cardModel)
            pivot.reparentTo(self.enemyHand)

        fan = fanHand(len(self.enemy.hand))
        for i, tr in enumerate(fan):
            addEnemyHandCard(tr)

        self.enemyHand.setPosHpr(2.5, -1.0, 7.1, 0, 45.0, 0)

    def makeBoard(self):
        """
        Show the player's faceups and facedowns
        """
        for i in self.playerFacedownNodes:
            i.detachNode()
        self.playerFacedownNodes = []
        for i in self.playerFaceupNodes:
            i.detachNode()
        self.playerFaceupNodes = []

        posX = 0.0
        posZ = 0.55

        def addFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-up')
            self.playerFaceupNodes.append(cardModel)

        def addFdCard(card):
            cardModel = self.loadPlayerBlank()
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-down')
            self.playerFacedownNodes.append(cardModel)

        for i in self.player.faceups:
            addFaceupCard(i)
            posX += 1.1
        for i in self.player.facedowns:
            addFdCard(i)
            posX += 1.1

    def makeEnemyBoard(self):
        for i in self.enemyFacedownNodes:
            i.detachNode()
        self.enemyFacedownNodes = []
        for i in self.enemyFaceupNodes:
            i.detachNode()
        self.enemyFaceupNodes = []

        posX = 0.0
        posZ = 2.1

        def addEnemyFdCard():
            cardModel = self.loadEnemyBlank()
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'enemy face-down')
            self.enemyFacedownNodes.append(cardModel)

        def addEnemyFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-up')
            self.enemyFaceupNodes.append(cardModel)

        for i in self.enemy.faceups:
            addEnemyFaceupCard(i)
            posX += 1.1
        for i in range(0, len(self.enemy.facedowns)):
            addEnemyFdCard()
            posX += 1.1

    def loadCard(self, card):
        cm = CardMaker(card.name)
        cardModel = self.render.attachNewNode(cm.generate())
        if card.owner == self.player:
            path = self.playerIconPath + "/" + card.image
        else:
            path = self.enemyIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        return cardModel

    def loadBlank(self, path):
        cm = CardMaker('mysterious card')
        cardModel = self.render.attachNewNode(cm.generate())
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        return cardModel

    def loadPlayerBlank(self):
        path = self.playerIconPath + "/" + self.playerCardBack
        return self.loadBlank(path)

    def loadEnemyBlank(self):
        path = self.enemyIconPath + "/" + self.enemyCardBack
        return self.loadBlank(path)

    def makePlayerFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.playerCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        self.playerFaceNode = cardModel

    def makeEnemyFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setTag('zone', 'face')
        self.enemyFaceNode = cardModel

    def playCard(self, handCard):
        if self.phase == Phase.reveal:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.playFaceup,
                self.playerHandNodes.index(handCard)
            )
        else:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.play,
                self.playerHandNodes.index(handCard)
            )
        self.makePlayerHand()
        self.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.revealFacedown,
            index
        )
        self.makePlayerHand()
        self.makeBoard()

    def attack(self, card, target):
        try:
            index = self.playerFaceupNodes.index(card)
        except ValueError:
            print("That card is not one of your faceups.")
            return
        targetIndex = 0
        zone = 0
        if target.getTag('zone') == 'face':
            if target == self.playerFaceNode:
                print("Can't attack yourself.")
                return
            zone = Zone.face
        elif target.getTag('zone') == 'enemy face-down':
            targetIndex = self.enemyFacedownNodes.index(target)
            zone = Zone.facedown
        else:
            if target in self.playerFaceupNodes:
                print("Can't attack your own faceups.")
                return
            targetIndex = self.enemyFaceupNodes.index(target)
            zone = Zone.faceup

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.attack,
            index,
            targetIndex,
            zone
        )

        self.makePlayerHand()
        self.makeBoard()
        self.makeEnemyBoard()

    def endPhase(self):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.endPhase
        )

    def redraw(self):
        self.makePlayerHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()
        self.endPhaseLabel.setText(str(Phase.keys[self.phase]))
        self.turnLabel.setText("Your Turn" if self.active else "Enemy Turn")
        if self.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()
        if self.phase == Phase.reveal and self.active:
            self.playerManaCapLabel.setText(
                str(self.player.mana) + " / " + str(self.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(self.player.manaCap))
        self.enemyManaCapLabel.setText(str(self.enemy.manaCap))

    def mouseOverTask(self, name):
        if self.mouseWatcherNode.hasMouse():
            if hasattr(self, 'cardNameLabel'):
                self.cardNameLabel.setText("")

            if hasattr(self, 'cardStatsLabel'):
                self.cardStatsLabel.setText("")

            if hasattr(self, 'tooltipLabel'):
                if hasattr(self, 'phase') and self.active:
                    self.tooltipLabel.setText(
                        "Reveal face-down cards" if self.phase == Phase.reveal
                        else "Play face-down cards and attack")
                else:
                    self.tooltipLabel.setText("")

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = self.playerIconPath + "/" + self.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            pickedObj = self.mouseHandler.getObjectClickedOn()
            if pickedObj:
                if pickedObj.getTag('zone') == 'hand':
                    card = self.player.hand[
                        self.playerHandNodes.index(pickedObj)]
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(
                        ("Instant. " if card.playsFaceUp else "") + card.desc)
                elif pickedObj.getTag('zone') == 'face-down':
                    card = self.player.facedowns[
                        self.playerFacedownNodes.index(pickedObj)]
                    self._activeObj = pickedObj
                    path = self.playerIconPath + "/" + card.image
                    pickedObj.setTexture(loader.loadTexture(path))
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'enemy face-down':
                    card = self.enemy.facedowns[
                        self.enemyFacedownNodes.index(pickedObj)]
                    if card is not None:
                        self._activeObj = pickedObj
                        path = self.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        label = str(card.cost) + " " + str(card.rank)
                        self.cardStatsLabel.setText(label)
                        self.tooltipLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'face-up':
                    if pickedObj in self.playerFaceupNodes:
                        card = self.player.faceups[
                            self.playerFaceupNodes.index(pickedObj)]
                    else:
                        card = self.enemy.faceups[
                            self.enemyFaceupNodes.index(pickedObj)]
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(card.desc)

        return Task.cont

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        return Task.cont


app = App(sys.argv)
app.camera.setPosHpr(4, -15, -15, 0, 45, 0)
app.run()
