qsub -v file='alibaba',model_file='alibaba',num_tasks='10',num_servers='10',extra='model sizing' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='30',num_servers='6',extra='task sizing' run_script.sh

qsub -v file='greedy',model_file='alibaba',num_tasks='10',num_servers='2',extra='full optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='15',num_servers='3',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='20',num_servers='4',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='30',num_servers='6',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='40',num_servers='8',extra='fixed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='50',num_servers='10',extra='time limited' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='75',num_servers='15',extra='time limited' run_script.sh

qsub -v file='alibaba',model_file='alibaba',num_tasks='10',num_servers='2',extra='foreknowledge flexible' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='15',num_servers='3',extra='foreknowledge fixed' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='20',num_servers='4',extra='foreknowledge fixed' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='30',num_servers='6',extra='foreknowledge fixed' run_script.sh
