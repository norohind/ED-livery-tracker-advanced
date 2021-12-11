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

insert_livery = """insert into livery (action_id, name, cur_price, orig_price, image_url) 
values 
(%(action_id)s, %(name)s, %(cur_price)s, %(orig_price)s, %(image)s);"""

insert_livery_timestamp = """insert into livery (action_id, name, cur_price, orig_price, image_url, timestamp) 
values 
(%(action_id)s, %(name)s, %(cur_price)s, %(orig_price)s, %(image)s, %(timestamp)s);"""

select_activity_pretty_names = """select 
to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as "Timestamp UTC",
action_id::bigint as "ActionId", 
items_count_new as "New Items count",
items_count_old as "Old Items count",
(items_count_new - items_count_old)::bigint as "Count Diff", 
sum_cur_price::bigint as "Sum Total",
sum_cur_price_old::bigint as "Sum Total Old", 
(sum_cur_price - sum_cur_price_old)::bigint as "Price Sum Diff" 
from 
    (
        select 
            sum_cur_price, 
            min(timestamp) as timestamp,
            min(items_count) as items_count_new,
            action_id, 
            lag (sum_cur_price, 1) over (order by sum_cur_price) sum_cur_price_old,
            lag (items_count, 1) over (order by items_count) items_count_old
        from (
                select 
                    sum(cur_price) as sum_cur_price, 
                    count(distinct name) as items_count, 
                    min(timestamp) as timestamp, 
                    action_id 
                from livery 
                group by action_id
             ) as foo
    group by sum_cur_price, action_id, items_count 
    order by timestamp desc 
    
    ) as foo1
where (sum_cur_price - sum_cur_price_old) != 0
limit %(limit)s;"""

select_diff_by_action_id = """select 
    coalesce(new_livery.name, 'Deleted Item') as "New Name",
    coalesce(old_livery.name, 'New Item') as "Old Name",
    new_livery.orig_price as "New Original Price",
    new_livery.cur_price as "New Current Price",
    old_livery.orig_price as "Old Original Price",
    old_livery.cur_price as "Old Current Price",
    new_livery.cur_price - old_livery.cur_price as "Current Price diff"
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
on new_livery.name = old_livery.name
where (new_livery.cur_price - old_livery.cur_price) <> 0 or (new_livery.cur_price - old_livery.cur_price) is null
order by new_livery.cur_price - old_livery.cur_price desc;"""