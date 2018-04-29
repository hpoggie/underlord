from panda3d.core import CollisionNode, GeomNode, CollisionRay
from direct.showbase.DirectObject import DirectObject

from core.core import Phase
from core.player import IllegalMoveError


class MouseHandler (DirectObject):
    def __init__(self):
        self.accept('mouse1', self.onMouse1, [])  # Left click
        self.accept('mouse3', self.onMouse3, [])  # Right click

        self.showCollisions = False

        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        base.cTrav.addCollider(pickerNP, base.handler)
        if self.showCollisions:
            base.cTrav.showCollisions(render)
        base.disableMouse()

        self.activeCard = None
        self._targeting = False

    @property
    def targeting(self):
        return self._targeting

    @targeting.setter
    def targeting(self, value):
        self._targeting = value
        if self._targeting:
            base.guiScene.showTargeting()
        else:
            base.guiScene.hideTargeting()

    def getObjectClickedOn(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            base.cTrav.traverse(render)
            if (base.handler.getNumEntries() > 0):
                base.handler.sortEntries()
                pickedObj = base.handler.getEntry(0).getIntoNodePath()
                pickedObj = pickedObj.findNetTag('zone')
                return pickedObj

    def doClick(self):
        pickedObj = self.getObjectClickedOn()

        if self.targeting:
            if pickedObj is not None:
                base.acceptTarget(pickedObj)
        elif pickedObj and not pickedObj.isEmpty():
            if pickedObj.getTag('zone') == 'hand':
                if not base.hasMulliganed:
                    c = pickedObj.getPythonTag('card')
                    if c in base.toMulligan:
                        base.toMulligan.remove(c)
                    else:
                        base.toMulligan.append(c)
                    base.zoneMaker.makePlayerHand()
                else:
                    base.playCard(pickedObj)
            elif pickedObj.getTag('zone') == 'face-down':
                if self.activeCard:
                    self.activeCard = None
                else:
                    base.revealFacedown(pickedObj)
            elif pickedObj.getTag('zone') == 'enemy face-down':
                if self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face-up':
                if base.phase == Phase.play and not self.activeCard:
                    self.activeCard = pickedObj
                elif self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face' and self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
        else:
            self.activeCard = None

    def onMouse1(self):
        try:
            self.doClick()
        except IllegalMoveError as e:
            print(e)

    def onMouse3(self):
        if self.targeting:
            base.acceptTarget(None)

    def mouseOverTask(self):
        if base.mouseWatcherNode.hasMouse():
            if hasattr(base.guiScene, 'redrawTooltips'):
                base.guiScene.redrawTooltips()

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = base.playerIconPath + "/" + base.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            pickedObj = self.getObjectClickedOn()
            if pickedObj:
                card = pickedObj.getPythonTag('card')
                if card is not None:
                    if pickedObj.getTag('zone') == 'hand':
                        base.guiScene.updateCardTooltip(card)
                    elif pickedObj.getTag('zone') == 'face-down':
                        self._activeObj = pickedObj
                        path = base.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        base.guiScene.updateCardTooltip(card)
                    elif pickedObj.getTag('zone') == 'enemy face-down':
                        self._activeObj = pickedObj
                        path = base.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        base.guiScene.updateCardTooltip(card)
                    elif pickedObj.getTag('zone') == 'face-up':
                        base.guiScene.updateCardTooltip(card)
