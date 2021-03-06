import textwrap

from panda3d.core import TransparencyAttrib
from panda3d.core import TextNode
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage

from core.game import Phase
from core.exceptions import IllegalMoveError

from client.zoneMaker import hideCard, showCard


commit_hash = ''


try:
    import git
    repo = git.Repo('.')
    # Get the hash of the latest commit
    commit_hash = repo.git.rev_parse('--short', 'HEAD')
except:  # If it doesn't work, don't worry about it
    pass


class Fonts(DirectObject):
    def __init__(self):
        self.titleFont = loader.loadFont("fonts/Cinzel-Regular.ttf")
        self.bodyFont = loader.loadFont("fonts/Ubuntu-Regular.ttf")
        self.titleFont.setPixelsPerUnit(120)
        self.bodyFont.setPixelsPerUnit(60)


class Scene(DirectObject):
    def __init__(self):
        self.titleFont = base.fonts.titleFont
        self.bodyFont = base.fonts.bodyFont

        # Put everything under one node to make it easy to destroy
        self.root = base.aspect2d.attachNewNode(name="GuiScene")

    def label(self, **kwargs):
        defaultArgs = {}
        # Attach the label to the root.
        # Note that this does not affect pos/scale for OnscreenText
        defaultArgs['parent'] = self.root
        defaultArgs['font'] = self.bodyFont  # Use the default font
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}  # Merge the 2 dicts; prefer kwargs
        return OnscreenText(**kwargs)

    def button(self, **kwargs):
        defaultArgs = {}
        # Attach the label to the root.
        # Note that this does not affect pos/scale for OnscreenText
        defaultArgs['parent'] = self.root
        defaultArgs['text_font'] = self.bodyFont  # Use the default font
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}  # Merge the 2 dicts; prefer kwargs
        return DirectButton(**kwargs)

    def image(self, **kwargs):
        defaultArgs = {}
        defaultArgs['parent'] = self.root
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}
        image = OnscreenImage(**kwargs)
        image.setTransparency(TransparencyAttrib.MAlpha)  # Enable alpha
        return image

    def unmake(self):
        self.root.detachNode()

    def showBigMessage(self, message):
        """
        Put huge text on the screen that obscures stuff
        """
        if hasattr(base, 'zoneMaker') and not base.hasMulliganed:
            base.zoneMaker.playerHand.hide()
        self.label(
            text=message,
            scale=(0.5, 0.5, 0.5))


class ConnectionUI(Scene):
    def __init__(self):
        super().__init__()
        self.connectingLabel = self.label(text="connecting to server")

    def showConnectionError(self, callback):
        self.connectingLabel.hide()
        self.connectionFailedLabel = self.label(
            text="Error. Could not connect to server")
        self.reconnectButton = self.button(
            pos=(0, 0, -0.25),
            image="./reconnect.png",
            relief=None,
            command=callback)


class MainMenu(Scene):
    def __init__(self):
        super().__init__()

        main = self.root.attachNewNode('main')

        self.label(
            text="UNDERLORD",
            font=self.titleFont,
            scale=0.3,
            pos=(0, 0.4, 0),
            parent=main)

        if commit_hash != '':
            self.label(
                text='latest commit: ' + commit_hash,
                pos=(0, 0.3, 0),
                parent=main)

        base.numPlayersLabel = self.label(
            text="Getting server info...",
            pos=(0, 0.2, 0),
            mayChange=True,
            parent=main)

        self.credits = self.root.attachNewNode('credits')

        def connect():
            base.connectionManager.startGame()

        def showCredits():
            if not hasattr(self, 'creditsLabel'):
                with open('CREDITS.txt') as f:
                    self.creditsLabel = self.label(
                        text='\n'.join(  # Don't wrap line breaks
                            textwrap.fill(line, width=60)
                            for line in f.read().split('\n')),
                        align=TextNode.ALeft,
                        scale=0.05,
                        pos=(-0.7, 0.5, 0),
                        parent=self.credits)

                self.button(
                    text="Back",
                    pos=(0, 0, -0.7),
                    parent=self.credits,
                    command=hideCredits)

            main.hide()
            self.credits.show()

        def hideCredits():
            main.show()
            self.credits.hide()

        def quit():
            base.userExit()

        buttons = (
            ("Play", connect),
            ("Credits", showCredits),
            ("Quit", quit))
        buttonPos = iter([
            (0, 0, len(buttons) * 0.15 - i * 0.15 - 0.5)
            for i in range(len(buttons))])
        for b in buttons:
            self.button(
                text=b[0],
                command=b[1],
                pos=next(buttonPos),
                frameSize=(-2, 2, -0.5, 1),
                parent=main)

    def showWaitMessage(self):
        self.label(
            text="Waiting for another player.",
            pos=(0, -0.5, 0))


class FactionSelect(Scene):
    def __init__(self):
        super().__init__()

        self.label(
            text="faction select",
            pos=(0, -0.7, 0),
            mayChange=True)

        icons = self.root.attachNewNode('icons')
        icons.setPos(-0.15 * len(base.availableFactions) / 2, 0, 0)

        for i, faction in enumerate(base.availableFactions):
            self.button(
                image=faction.iconPath + '/' + faction.cardBack,
                parent=icons,
                pos=(i * 0.2, 0, 0),
                relief=None,
                command=base.pickFaction,
                extraArgs=[i])

    def showWaitMessage(self):
        self.label(
            text="Waiting for opponent.",
            pos=(0, -0.5, 0))


class GoingFirstDecision(Scene):
    def __init__(self):
        super().__init__()

        self.button(
            text="Go first",
            pos=(0, 0, 0.1),
            command=base.goFirst)
        self.button(
            text="Go second",
            pos=(0, 0, -0.1),
            command=base.goSecond)


class GameHud(Scene):
    def __init__(self):
        super().__init__()

        self.turnLabel = self.label(
            text="",
            pos=(0, -0.9, 0),
            mayChange=True)

        self.playerManaCapLabel = self.label(
            text=str(base.player.manaCap),
            pos=(-0.7, -0.44, 0),
            mayChange=True)
        self.enemyManaCapLabel = self.label(
            text=str(base.enemy.manaCap),
            pos=(-0.5, 0.8),
            mayChange=True)
        self.cardNameLabel = self.label(
            text="",
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = self.label(
            text="",
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = self.label(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = self.label(
            text="",
            pos=(0.7, -0.7, 0),
            mayChange=True)
        self.endPhaseButton = self.button(
            text="End Phase",
            pos=(0.7, 0, -0.85),
            command=self.onEndPhaseButton)
        self.mulliganButton = self.button(
            text="Mulligan",
            pos=(0.7, 0, -0.85),
            command=self.onMulliganButton)

        self.redraw()

    def onMulliganButton(self):
        base.mulligan()

    def onEndPhaseButton(self):
        try:
            base.endPhase()
        except IllegalMoveError as e:
            print(e)

    def hideBigMessage(self):
        base.zoneMaker.playerHand.show()  # hidden by showBigMessage
        if hasattr(self, 'winLabel') and self.winLabel is not None:
            self.winLabel.detachNode()

    def showTargeting(self):
        if not hasattr(self, 'targetingLabel'):
            self.targetingLabel = self.label(
                pos=(0, 0, 0),
                mayChange=True)
            self.targetingGradient = self.image(
                image="gradient.png",
                pos=(0, -0.7, 0),
                scale=(10, 1, 3))
        else:
            self.targetingLabel.show()
            self.targetingGradient.show()

        self.targetingLabel.setText(base.targetDesc.split('\n')[0])

    def hideTargeting(self):
        self.targetingLabel.hide()
        self.targetingGradient.hide()

    def redrawTooltips(self):
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

    def redraw(self):
        if base.hasMulliganed:
            self.mulliganButton.detachNode()
            self.endPhaseLabel.setText(str(Phase.keys[base.phase]))
        else:
            self.endPhaseLabel.setText("Mulligan")

        # Hide everything if we haven't mulliganed yet
        if not base.bothPlayersMulliganed:
            self.endPhaseButton.hide()
            self.playerManaCapLabel.setText("")
            self.enemyManaCapLabel.setText("")
            return

        if base.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()

        if base.phase == Phase.reveal and base.active:
            self.playerManaCapLabel.setText(
                str(base.player.mana) + " / " + str(base.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(base.player.manaCap))

        self.enemyManaCapLabel.setText(str(base.enemy.manaCap))
        self.turnLabel.setText("Your Turn" if base.active else "Enemy Turn")

    def startReplacing(self, nTargets):
        targets = []

        def callback(target):
            if target in targets:
                targets.remove(target)
                if target is not None:
                    showCard(target)
            else:
                targets.append(target)
                if target is not None:
                    hideCard(target)

            if len(targets) == nTargets:
                base.replace(targets)
                base.finishTargeting()

        # TODO: base on desc for effect
        base.mouseHandler.startTargeting("Select targets", callback)
