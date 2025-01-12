(define (domain robotics)
  (:requirements :strips :equality)
  (:constants door blf_trayLoc2)
  (:predicates
	   (Location ?loc)
	   (At ?obj ?loc)
           (RobotAt ?loc)
	   (InGripper ?obj)
	   (IsAccessPointFor ?loc ?targetLocation)
	   (Obstructs ?loc ?obj ?obj)
	   (IsGP ?loc ?obj)
	   (Object ?obj)
	   (OnTray ?obj)
	   (IsTray ?tray)
	   (IsAccessPointForTray ?loc ?tray)
	   (Topmost ?obj ?tray)
	   (Heavy ?tray)
	   (Bigger ?obj1 ?obj2)
	   (On ?obj1 ?obj2)
	   (TempArea ?loc)
	   (TrayLocation ?loc)
	   (InRoom1 ?loc)
	   (InRoom2 ?loc)
  )


 (:action placeOnTray
   :parameters(?lrobot ?obj1 ?obj2 ?tray ?trayloc)
   :precondition(and (Location ?lrobot) (Object ?obj1) (Object ?obj2)
   		     (RobotAt ?lrobot) (IsTray ?tray) 
		     (At ?tray ?trayloc)
   		     (IsAccessPointFor ?lrobot ?trayloc) (InGripper ?obj1) 
		     (Topmost ?obj2 ?tray) (not (Bigger ?obj1 ?obj2)))
   :effect(and (not (InGripper ?obj1)) (OnTray ?obj1) (on ?obj1 ?obj2)
   	       (not (Topmost ?obj2 ?tray)) (Topmost ?obj1 ?tray) )
 )	      

 (:action pickTray
  :parameters(?lrobot ?tray ?trayloc)
  :precondition(and (RobotAt ?lrobot) (IsTray ?tray)
  		    (forall (?o) (not (InGripper ?o)))
		    (IsAccessPointFor ?lrobot ?trayloc)
		    (At ?tray ?trayloc)
		    (not (Heavy ?tray)))
  :effect(and (InGripper ?tray) (not (At ?tray ?trayloc)))
 )

 (:action pickFromTray
  :parameters(?lrobot ?tray ?obj ?obj2 ?trayloc)
  :precondition(and (Location ?lrobot) (IsTray ?tray) (Object ?obj)
  		  (RobotAt ?lrobot) (IsAccessPointFor ?lrobot ?trayloc)
		  (At ?tray ?trayloc)
		  (Topmost ?obj ?tray) (on ?obj ?obj2)
		  (forall (?o) (imply (Object ?o) (not (InGripper ?o))))
		  )
  :effect(and (InGripper ?obj) (not (Heavy ?tray)) (not (ontray ?obj))
  	      (not (Topmost ?obj ?tray)) (not (on ?obj ?obj2))
	      (topmost ?obj2 ?tray)
	      )
)

 (:action putDownTray
  :parameters(?lrobot ?tray ?ltarget)
  :precondition (and (IsTray ?tray) (Location ?lrobot)
  		     (InGripper ?tray) (TrayLocation ?ltarget)
		     (RobotAt ?lrobot) (IsAccessPointFor ?lrobot ?ltarget))
  :effect (and (not (InGripper ?tray)) (At ?tray ?ltarget))
 )


 (:action putDown
  :parameters(?o1 ?l1 ?l2)
  :precondition (and (Object ?o1) (Location ?l1) (Location ?l2) 
  		     (InGripper ?o1) (RobotAt  ?l2) (TempArea ?l1)
		     (IsAccessPointFor ?l2 ?l1))
  :effect (and (not (InGripper ?o1)) (At ?o1 ?l1) )
 )


  (:action moveToWithinR1
     :parameters(?l1 ?l2)
     :precondition (and (Location ?l1) (Location ?l2) (RobotAt ?l1)
     		   	(InRoom1 ?l1) (InRoom1 ?l2)
     		   	)
     :effect (and (not (RobotAt ?l1)) (RobotAt ?l2))
  )

  (:action moveToWithinR2
     :parameters(?l1 ?l2)
     :precondition (and (Location ?l1) (Location ?l2) (RobotAt ?l1)
     		   	(InRoom2 ?l1) (InRoom2 ?l2)
     		   	)
     :effect (and (not (RobotAt ?l1)) (RobotAt ?l2))
  )

  (:action moveToAcrossRooms
     :parameters(?l1 ?l2 ?tray)
     :precondition (and (Location ?l1) (Location ?l2) (RobotAt ?l1)
     		   	(InGripper ?tray)
     		   	)
     :effect (and (not (RobotAt ?l1)) (RobotAt ?l2))
  )

  



 (:action grasp
     :parameters(?o1 ?l1 ?l2)
     :precondition(and (Object ?o1) (Location ?l1) (Location ?l2) (At  ?o1 ?l1) 
     		       (RobotAt ?l2) (IsGP ?l2 ?o1)
		       (forall (?o) (not (InGripper ?o)))  
		       (forall (?o) (imply (Object ?o) 
		       	       	    (not (Obstructs ?l2 ?o ?o1)) ))
		       )
     :effect (and (InGripper ?o1) (not (At ?o1 ?l1))
     	     (forall (?o) (forall (?l) (not (Obstructs ?l ?o1 ?o))))
	     )
 )
)
