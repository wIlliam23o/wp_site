#!/bin/bash

# Fixes the incrementing id on django database tables.
# Any time a database is imported, restored you may encounter a
# 'duplicate pkey' or 'duplicate id' error.
# This script runs the needed SQL to fix the id.

# (Basically it increments the nextval() to the TABLE's max id + 1.)

# Tables to modify
tables=("blogger_wp_blog" "projects_wp_project" "django_admin_log" "downloads_file_tracker" "auth_permission" "django_content_type")

# FUNCTIONS -------------------------------------------------------------------
function print_usage () {
    echo "usage: wp-db-fix.sh [options] database_name"
    echo "    options:"
    echo "        -h : show this help message"
    echo "        -d : dry-run, only show what is going to be executed."
    echo ""
}

function print_noargs () {
    echo "You did not enter a database name to fix."
    echo "    Expecting: ./wp-db-fix.sh [options] database_name"
    printf "\n* Tables to fix:\n"
    printf "        %s\n" "${tables[@]}"
}
   
# MAIN ENTRY POINT ------------------------------------------------------------
# No args
if [ "${1}" == "" ]; then
    print_noargs
    exit 1
fi

# Check args
dryrun="false"
dbname=""
for arg in "${@}"
do
    # check for flags
    if [[ "$arg" == -* ]]; then
        # get help flag
        if [[ "$arg" == -h* ]] || [[ "$arg" == --h* ]]; then
            print_usage
            exit 0
        # get dryrun flag
        elif [[ "$arg" == -d* ]] || [[ "$arg" == --d* ]]; then
            dryrun="true"
        fi
    else
        # non-flag, use it as the database name.
        dbname="${arg}"
    fi
done

# Check database name is set.
if [ "$dbname" == "" ]; then
    printf "No database name given!\n\n"
    print_usage
    exit 1
fi

# get user (use currently logged in user for database access)
user_=$USER
if [ "$user_" == "" ]; then
    user_=$LOGNAME
    if [ "$user_" == ""]; then
        printf "\nCan't find user name!"
        exit 1
    fi
fi

# psql command for executing SQL commands
psql_cmd="psql -U ${user_} -d ${dbname} --command="

# Execute SQL
if [ "$dryrun" == "true" ]; then

    # Just show what is going to be executed.
    printf "%s\n" "${psql_cmd}"
    for tablename in "${tables[@]}"
    do
        sql_="SELECT SETVAL('${tablename}_id_seq', SELECT MAX(id) from ${tablename}) + 1);"
        printf "    %s\n" "${sql_}"
    done
else
    # Actually Execute.

    # Build SQL command
    for tablename in "${tables[@]}"
    do
        sql_="SELECT SETVAL('${tablename}_id_seq', (SELECT MAX(id) from ${tablename}) + 1);"
        fullcmd="${psql_cmd}${sql_}"
        echo "Executing SQL: "
        echo "    ${fullcmd}"
        results=`$psql_cmd`$sql_
        
        if [ "$results" == "" ]; then
            printf "    No response returned!\n"
        else
            if [ "${results:0:6}" == "SELECT" ]; then
            	printf "    Success for: %s\n" "$tablename"
            else
            	printf "    Weird response for: %s\n" "$tablename"
            	printf "        %s" "$results"
            fi
        fi
    done

fi

# FINISHED
printf "\nFinished SQL for database: %s\n" "${dbname}"