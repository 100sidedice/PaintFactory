Set up base UI for machine selection
    - Create a container for the machine selection sidebar
    - Create a component in which displays a machine (similar to image)
    - Turn that into a sidebar
Assign data to the sidebar
    - When we click any of them, push a Select event
    - If selected machine = sidebar index, green outline, else no outline
    - If click a selected event, set selected to 0

Selected to world
    - If we have a machine selected, then click on the world (nothing covering it), place a machine.
    - Machines should be clickable.  Blue outline on selected machines. 
    - If we right click a machine, open a popup menu with [Open, Select, Rotate, Delete]
    - If we drag a machine, rotate it based on mouse angle
    - If we double tap a machine, open it's menu
