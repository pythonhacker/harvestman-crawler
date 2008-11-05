#Generate epydoc documentation from harvest man.
#Required epydoc >2.0
#Run as: sh harvestman-epydoc.sh
epydoc -v -o harvestman-epydoc --name epydoc --css white                  --url http://localhost/ --inheritance listed  --graph classtree ../harvestman --no-frames
