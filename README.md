# Elastic Resource allocation for Edge Cloud Computing

This research was primarily completed during the summer of 2019 under the supervisor of Dr Sebastian Stein within the 
Agent Interactions and Complexity research group at the University of Southampton. The work has finished over the summer
of 2020 with the aims of publishing this research, which can be found in the paper folder of this project. 

This research investigates a modification to the standard resource allocation mechanism in cloud computing through
utilising the idea that the time taken for an operation to occur is proportional to resource allocated for the task.
This principle is referred to as "flexible resource allocation". An example of this principle is the loading or 
sending results to/from a user as the amount of bandwidth allocated for the operation is proportional to the time 
taken for the operation to occur.   

Because of this modification to the standard resource allocation optimisation formulae means that all previous research
is incompatible with our elastic resource allocation optimisation formulation. Therefore in this work we present three
different mechanisms: greedy algorithm, critical value auction and decentralised iterative auction.   