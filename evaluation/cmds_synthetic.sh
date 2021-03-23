qsub -v file='greedy',model_file='synthetic',num_tasks='10',num_servers='2',extra='full optimal' run_script.sh
qsub -v file='greedy',model_file='synthetic',num_tasks='15',num_servers='3',extra='full optimal' run_script.sh
qsub -v file='greedy',model_file='synthetic',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='synthetic',num_tasks='30',num_servers='6',extra='time limited' run_script.sh
qsub -v file='greedy',model_file='synthetic',num_tasks='40',num_servers='8',extra='time limited' run_script.sh

qsub -v file='greedy',model_file='synthetic',num_tasks='40',num_servers='8',extra='lower bound' run_script.sh

qsub -v file='auctions',model_file='synthetic',num_tasks='10',num_servers='2',extra='full optimal' run_script.sh
qsub -v file='auctions',model_file='synthetic',num_tasks='15',num_servers='3',extra='full optimal' run_script.sh
qsub -v file='auctions',model_file='synthetic',num_tasks='15',num_servers='3',extra='fixed optimal' run_script.sh
qsub -v file='auctions',model_file='synthetic',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='auctions',model_file='synthetic',num_tasks='30',num_servers='6',extra='time limited' run_script.sh
qsub -v file='auctions',model_file='synthetic',num_tasks='40',num_servers='8',extra='time limited' run_script.sh

qsub -v file='resource_ratio',model_file='synthetic',num_tasks='15',num_servers='3' run_script.sh
qsub -v file='resource_ratio',model_file='synthetic',num_tasks='15',num_servers='3',extra='fixed optimal' run_script.sh
qsub -v file='resource_ratio',model_file='synthetic',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='resource_ratio',model_file='synthetic',num_tasks='40',num_servers='8' run_script.sh

qsub -v file='dia_heuristics',model_file='synthetic',num_tasks='30',num_servers='6' run_script.sh
qsub -v file='dia_heuristics',model_file='synthetic',num_tasks='30',num_servers='6',extra='non uniform heuristics' run_script.sh

qsub -v file='online',model_file='online_synthetic',num_servers='6' run_script.sh
qsub -v file='online',model_file='online_synthetic',num_servers='8' run_script.sh

qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',extra='task mutation' run_script.sh
qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',extra='dia repeat' run_script.sh

qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',repeat='0',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',repeat='1',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',repeat='2',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',repeat='3',extra='mutation grid search' run_script.sh

qsub -v file='mutation',model_file='synthetic',num_tasks='30',num_servers='6',extra='special case' run_script.sh

qsub -v file='evolution_strategy',model_file='synthetic',num_tasks='30',num_servers='6' run_script.sh