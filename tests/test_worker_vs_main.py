import unittest

class RBush:
    def __init__(self):
        self.items = []

    def load(self, items):
        self.items.extend(items)

    def search(self, bbox):
        return [i for i in self.items if not (i['maxX'] < bbox['minX'] or i['minX'] > bbox['maxX'] or i['maxY'] < bbox['minY'] or i['minY'] > bbox['maxY'])]

class WorkerVsMainTest(unittest.TestCase):
    def test_search_same(self):
        items = [
            {'minX':0,'minY':0,'maxX':1,'maxY':1,'id':1},
            {'minX':2,'minY':2,'maxX':3,'maxY':3,'id':2}
        ]
        tree = RBush()
        tree.load(items)
        bbox = {'minX':0,'minY':0,'maxX':2.5,'maxY':2.5}
        rb = {i['id'] for i in tree.search(bbox)}
        linear = {i['id'] for i in items if not (i['maxX']<bbox['minX'] or i['minX']>bbox['maxX'] or i['maxY']<bbox['minY'] or i['minY']>bbox['maxY'])}
        self.assertEqual(rb, linear)

if __name__ == '__main__':
    unittest.main()
