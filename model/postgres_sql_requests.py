schema_create = """create table if not exists livery (
action_id integer,
name text,
cur_price integer,
orig_price integer,
image_url text,
timestamp timestamp default timezone('utc', now()));

--create index if not exists idx_action_id_0 on squads_stats_states (action_id);
--create index if not exists idx_platform_leaderboard_type_1 on squads_stats_states(platform, leaderboard_type);
"""

select_last_action_id = """select action_id 
from livery
order by action_id desc
limit 1;"""

insert_leader_board = """insert into livery (action_id, name, cur_price, orig_price, image_url) 
values 
(%(action_id)s, %(name)s, %(cur_price)s, %(orig_price)s, %(image)s);"""

insert_leader_board_timestamp = """insert into livery (action_id, name, cur_price, orig_price, image_url, timestamp) 
values 
(%(action_id)s, %(name)s, %(cur_price)s, %(orig_price)s, %(image)s, %(timestamp)s);"""

select_activity_pretty_names = """select 
sum_score::bigint as "TotalExperience", 
to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as "Timestamp UTC",
action_id::bigint as "ActionId", 
sum_score_old::bigint as "TotalExperienceOld", 
(sum_score - sum_score_old)::bigint as "Diff" 
from 
    (
        select 
            sum_score, 
            min(timestamp) as timestamp, 
            action_id, 
            lag (sum_score, 1) over (order by sum_score) sum_score_old 
        from (
                select sum(cur_price) as sum_score, min(timestamp) as timestamp, action_id 
                from livery 
                group by action_id
             ) as foo
    group by sum_score, action_id 
    order by timestamp desc 
    
    ) as foo1
where (sum_score - sum_score_old) <> 0 
limit %(limit)s;"""

select_diff_by_action_id = """select 
    new_livery.name as new_name,
    old_livery.name as old_name,
    new_livery.orig_price as new_orig_price,
    new_livery.cur_price as new_cur_price,
    old_livery.orig_price as old_orig_price,
    old_livery.cur_price as old_cur_price,
    new_livery.cur_price - old_livery.cur_price
from (
    select * 
    from livery 
    where action_id = %(action_id)s) new_livery 
full join 
    (
        select * 
        from livery 
        where action_id = %(action_id)s - 1
    ) old_livery 
on new_livery.name = old_livery.name;"""