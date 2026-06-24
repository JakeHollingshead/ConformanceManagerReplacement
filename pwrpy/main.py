
from unittest import result

import sqlite3

def get_db_connection():
    conn = sqlite3.connect("CRIMan.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA timeout=5")
    return conn

conn = get_db_connection()
mfrs = conn.execute("SELECT * FROM Manufacturer").fetchall()
mds = conn.execute("""
    SELECT m.md_id, m.md_name, m.md_make, m.md_type, m.md_size, m.md_endsize,
            m.md_mfr_id, mfr.mfr_name, m.md_description
    FROM models m
    LEFT JOIN Manufacturer mfr ON m.md_mfr_id = mfr.mfr_id
""").fetchall()
conn.close()

print(mfrs)
print(mds)



# print(True + True + True - False)


# expression = input("values for eval")

# result = eval(expression)

# print(result)
# ------------Test Range area-------------


# nums=range(1,1000)

# def is_prime(num):
#     for x in range(2,num):
#         if (num%x) == 0:
#             return False
#         return True
    
# primes=list(filter(is_prime, nums))
       
# # print(primes)

# # ------------Test Range area-------------

# a = [1,2,3,4,5,6,7,8,9]
# b = [4,4,2,2,4,6,0,8,11]

# def merge_array (arrayA, ArrayB):
#     return sorted(set(arrayA) | set(ArrayB))

# print(merge_array(a,b))

# a1 = [1,2,3,4,5,6,7,8,9]
# b1 = [4,4,2,2,4,6,0,8,11]

# def merge_array1 (arrayA, ArrayB):
#     return sorted(set(arrayA + ArrayB))

# print(merge_array1(a1,b1))