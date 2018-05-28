# def factorial(num):
#     if num == 1:
#         print "End"
#         return 1
#     else:
#         print str(num) + "*" + "factorial(" + str(num-1) + ")"
#         return num * factorial(num-1)
#
#
# # print factorial(5)
#
# data = {
#     "A1": {
#         "A2": {
#             "A3": {
#
#             }
#         }
#     },
#     "B1": {
#         "B2": {
#             "B3": {
#
#             }
#         }
#     }
# }
#
#
# def data_print(data):
#     for key in data:
#         print key
#         data_print(data[key])



class Testing:
    def __init__(self):
        self.inherit = []

    def test1(self):
        self.inherit.append([1,2,3,4,5])

    def test2(self):
        self.inherit.append([4,5,6,7,8])

    def printing(self):
        print self.inherit

class Inherit(Testing):
    def __init__(self):
        Testing.__init__(self):
        pass

    def printer(self):
        print self.inherit


test = Testing()
test.test1()
test.printing()
test2 = Inherit()
test2.printing()
