qsub -v file='alibaba',model_file='alibaba',num_tasks='10',num_servers='10',extra='model sizing' run_script.sh

qsub -v file='greedy',model_file='alibaba',num_tasks='10',num_servers='2',extra='full optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='15',num_servers='3',extra='full optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='20',num_servers='4',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='50',num_servers='10',extra='time limited' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='75',num_servers='15',extra='time limited' run_script.sh

qsub -v file='auctions',model_file='alibaba',num_tasks='10',num_servers='2',extra='full optimal' run_script.sh
qsub -v file='auctions',model_file='alibaba',num_tasks='15',num_servers='3',extra='full optimal' run_script.sh
qsub -v file='auctions',model_file='alibaba',num_tasks='20',num_servers='4',extra='fixed optimal' run_script.sh
qsub -v file='auctions',model_file='alibaba',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='auctions',model_file='alibaba',num_tasks='50',num_servers='10',extra='time limited' run_script.sh
qsub -v file='auctions',model_file='alibaba',num_tasks='75',num_servers='15',extra='time limited' run_script.sh

qsub -v file='resource_ratio',model_file='alibaba',num_tasks='25',num_servers='5',extra='full optimal' run_script.sh
qsub -v file='resource_ratio',model_file='alibaba',num_tasks='25',num_servers='5',extra='fixed optimal' run_script.sh

qsub -v file='dia_heuristics',model_file='alibaba',num_tasks='25',num_servers='5' run_script.sh
qsub -v file='dia_heuristics',model_file='alibaba',num_tasks='25',num_servers='5',extra='non uniform heuristics' run_script.sh

qsub -v file='online',model_file='alibaba',num_servers='6' run_script.sh
qsub -v file='online',model_file='alibaba',num_servers='8' run_script.sh

qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',extra='task mutation' run_script.sh
qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',extra='dia repeat' run_script.sh

qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',repeat='0',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',repeat='1',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',repeat='2',extra='mutation grid search' run_script.sh
qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',repeat='3',extra='mutation grid search' run_script.sh

qsub -v file='mutation',model_file='alibaba',num_tasks='30',num_servers='6',extra='special case' run_script.sh

qsub -v file='evolution_strategy',model_file='alibaba',num_tasks='30',num_servers='6' run_script.sh
