class Card:
    name = "Placeholder Name"
    image = "concentric-crescents.png"
    cost = 0
    rank = 0
    spell = False

    def __init__ (self, attributes):
        self.__dict__ = attributes.copy()

    def exposed_getName (self):
        return self.name

    def exposed_getImage (self):
        return self.image

    def exposed_getCost (self):
        return self.cost

    def exposed_getRank (self):
        return self.rank

    def __print__ (self):
        print self.name + " cost " + cost

class Faction:
    name = "My Faction"
    iconPath = "./my_faction_icons"
    cardBack = "my-faction-back.png"
    deck = []

    def __init__ (self, attributes):
        self.__dict__ = attributes.copy()

def one ():
    return Card({
        'name': "One",
        'image': "dice-six-faces-one.png",
        'cost': 1,
        'rank': 1
        })

def two ():
    return Card({
        'name': "Two",
        'image': "dice-six-faces-two.png",
        'cost': 2,
        'rank': 2
        })

def three ():
    return Card({
        'name': "Three",
        'image': "dice-six-faces-three.png",
        'cost': 3,
        'rank': 3
        })

def four ():
    return Card({
        'name': "Four",
        'image': "dice-six-faces-four.png",
        'cost': 4,
        'rank': 4
        })

def five ():
    return Card({
        'name': "Five",
        'image': "dice-six-faces-five.png",
        'cost': 5,
        'rank': 5
        })
