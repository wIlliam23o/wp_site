#!/bin/bash

# Fixes the incrementing id on django database tables.
# Any time a database is imported or restored you may encounter a
# 'duplicate pkey' or 'duplicate id' error.
# This script runs the needed SQL to fix the id.

# (Basically it increments the nextval() to the TABLE's max id + 1.)

# Warning: This hasn't been tested since wp_site 1.0.0.

# Tables to modify (This is specific to this project)
tables=(
    "blogger_wp_blog"
	"projects_wp_project"
	"django_admin_log"
	"downloads_file_tracker"
	"auth_permission"
	"django_content_type"
)

# FUNCTIONS -------------------------------------------------------------------
function print_usage () {
    echo "
    Usage:
        wp-db-fix.sh [options] database_name

    Options:
        -h : show this help message
        -d : dry-run, only show what is going to be executed.
"
}

function print_noargs () {
    echo "You did not enter a database name to fix."
    echo "    Expecting: ./wp-db-fix.sh [options] database_name"
    echo -e "\n* Tables to fix:\n"
    printf "        %s\n" "${tables[*]}"
}

# MAIN ENTRY POINT ------------------------------------------------------------
# No args
if [[ -z "$1" ]]; then
    print_noargs
    exit 1
fi

# Check args
dryrun=false
dbname=""
for arg
do
    # check for flags
    if [[ "$arg" =~ ^(-h)|(--help)$ ]]; then
        # get help flag
        print_usage
        exit 0
        # get dryrun flag
    elif [[ "$arg" =~ ^(-d)|(--dryrun)$ ]]; then
        dryrun=true
    else
        # non-flag, use it as the database name.
        dbname="${arg}"
    fi
done

# Check database name is set.
if [[ -z "$dbname" ]]; then
    printf "No database name given!\n\n"
    print_usage
    exit 1
fi

# get user (use currently logged in user for database access)
user_=$USER
if [[ -z "$user_" ]]; then
    user_=$LOGNAME
    if [[ -z "$user_" ]]; then
        printf "\nCan't find user name!"
        exit 1
    fi
fi

# psql command for executing SQL commands
psql_args=("-U" "$user_" "-d" "$dbname" "--command=")

# Execute SQL
if [[ $dryrun == true ]]; then

    # Just show what is going to be executed.
    printf "%s %s\n" "psql" "${psql_args[*]}"
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
        fullcmdstr="psql ${psql_args[*]} $sql_"
        echo "Executing SQL: "
        echo "    ${fullcmdstr}"
        results="$(psql "${psql_args[@]}" "$sql_")"

        if [[ -z "$results" ]]; then
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
