def factorial(num):
    if num == 1:
        print "End"
        return 1
    else:
        print str(num) + "*" + "factorial(" + str(num-1) + ")"
        return num * factorial(num-1)


# print factorial(5)

data = {
    "A1": {
        "A2": {
            "A3": {

            }
        }
    },
    "B1": {
        "B2": {
            "B3": {

            }
        }
    }
}


def data_print(data):
    for key in data:
        print key
        data_print(data[key])

data_print(data)