# DrawPI
DrawPi : traceur pendulaire, autonome et minimaliste à base de raspberry DrawPi, le traceur pendulaire autonome et minimaliste à base de Raspberry Pi.
(mots clefs : #raspberrypi #drawbot #diy #verticalplotter #28BYJ-48)

"v_potter.py"
la partie v plotter prend en entrée un fichier au format dérivé du format svg (cela permet de prévisualiser avec un navigateur ou avec inkscape), par contre c'est un sous ensemble très limité du svg...exclusivement restreint au chemins (paths) avec des coordonnées absolues. ex pour dessiner un carré:

"<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" name="image_contour.svg">
  <path fill="none" stroke="black" d="M 10 0 L 200 0 L 200 200 L 0 200 L 0 0 L 10 0 " />
</svg>"

