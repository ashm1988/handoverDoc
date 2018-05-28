class meh:
    def __init__(self):
        self.inherit = []

    def test1(self):
        self.inherit.append([1,2,3,4,5])

    def test2(self):
        self.inherit.append([4,5,6,7,8])

    def printing(self):
        print self.inherit

class Inherit(meh):
    def __init__(self):
        meh.__init__(self)

    def printer(self):
        print self.inherit


test = meh()
# test.test1()
test.test2()
test.test1()
test.printing()
test = Inherit()
test.printer()

