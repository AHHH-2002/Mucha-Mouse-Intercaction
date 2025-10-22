Mucha-style Mouse Interaction Game: Vine Blossoms
Implemented with Pygame, its core feature is generating Mucha-style vines and flowers through mouse movement — the movement trail transforms into smooth vines, with speed controlling the thickness of the vines and the density of the flowers. Clicking switches the background color, perfectly recreating the signature elements of "curvilinear rhythm + ornamental flowers" in Mucha's works.

Operation Guide  
Sliding the mouse: Generates Mucha-style vines and flowers (slow sliding = thin vines + dense flowers; fast sliding = thick vines + sparse flowers).  
Left-click: Switches the background color (cycles through off-white → lavender → cyan-green).  
Press the S key: Saves the current screen to the local device (saved in the same folder where the code is running).  
Close the window: Exits the game.

Vine Gradual Fading:  
Each trail point decreases in transparency over time (with the alpha value dropping from 255 to 0), causing old trails to fade gradually.  
When the transparency reaches 0, the trail points are automatically removed, keeping the screen clean at all times and preventing excessive accumulation of elements.  
The transparency of vines and flowers changes synchronously to ensure visual consistency.
