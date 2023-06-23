#declare variables
average = 0
x = 0
results = []
area = 162326.8
tot_area = 0

#open file with output log from pi
f = open("results.txt", "r")

#processes file line by line
for line in f:
#split name from certainty percentage
  split = line.split(" ")
#only proceed with results other than night/twilight
  if split[0] != "nightAndTwilight":
#for cloud images
    if split[0] == "clouds":
      print(split[1])
#add certainty value to average
      average += float(split[1])
#take any result other than clouds as 0
    else:
      average += 0
    x += 1
    if x > 3:
      x = 0
#calculate average
      average /= 4
#append average to list
      results.append(average)
#reset average
      average = 0

f.close()

#print list containing new certainty percentages
print(results)    
x = 0
#for each result in the list
while x < len(results):
#calculate area of clouds per result and add to total cloud area
  tot_area += (results[x] * area)
  print(tot_area)
#move to next item in list
  x += 1

print(tot_area)
