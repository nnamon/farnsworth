set client_min_messages to WARNING;

-- TODO: rename _type to _kind to prevent name clashes

start transaction;

-- Trees
create extension ltree;

---------------------------------------------------------------------

-- Teams
drop table if exists teams;
create table teams (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    name varchar(256) not null
);

-- Challenge Sets
drop table if exists challenge_sets;
create table challenge_sets (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    name varchar(256) not null
);

-- Challenge Binary Nodes
drop table if exists challenge_binary_nodes;
create table challenge_binary_nodes (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    root_id bigint null,
    parent_id bigint null,
    parent_path ltree null,
    name varchar(256) not null,
    cs_id bigint not null references challenge_sets (id),
    submitted_at timestamp null,
    patch_type varchar(256) null,
    blob bytea
);

-- We have to create the self-references here because of inheritance.
alter table challenge_binary_nodes add
    foreign key (root_id) references challenge_binary_nodes (id);

alter table challenge_binary_nodes add
    foreign key (parent_id) references challenge_binary_nodes (id);

-- Jobs
drop table if exists jobs;
create table jobs (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    priority int not null,
    worker varchar(256) not null,
    limit_cpu int null,
    limit_memory int null,  -- In MiB
    limit_time int null,    -- In Seconds
    started_at timestamp null,
    completed_at timestamp null,
    cbn_id bigint null references challenge_binary_nodes (id),
    produced_output boolean null,
    payload jsonb
);

-- Tests
drop table if exists tests;
create table tests (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cbn_id bigint not null references challenge_binary_nodes (id),
    job_id bigint not null references jobs (id),
    drilled boolean not null,
    colorguard_traced boolean not null,
    poll_created boolean not null,
    blob bytea
);

-- Crashes
drop type if exists crash_kind;
create type crash_kind as enum('unclassified',
                               'unknown',
                               'ip_overwrite',
                               'partial_ip_overwrite',
                               'uncontrolled_ip_overwrite',
                               'bp_overwrite',
                               'partial_bp_overwrite',
                               'write_what_where',
                               'write_x_where',
                               'uncontrolled_write',
                               'arbitrary_read',
                               'null_dereference');

drop table if exists crashes;
create table crashes (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cbn_id bigint not null references challenge_binary_nodes (id),
    job_id bigint not null references jobs (id),
    triaged boolean not null,
    explorable boolean null,
    explored boolean null,
    exploitable boolean null,
    exploited boolean null,
    blob bytea,
    kind crash_kind not null
);

-- Exploits
drop type if exists pov_type;
create type pov_type as enum('type1', 'type2');

drop type if exists exploitation_method;
create type exploitation_method as enum('unclassified', 'circumstantial',
                                        'shellcode', 'rop');

drop table if exists exploits;
create table exploits (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cbn_id bigint not null references challenge_binary_nodes (id),
    job_id bigint not null references jobs (id),
    pov_type pov_type not null,
    exploitation_method exploitation_method not null,
    submitted_at timestamp null,
    submitted_teams varchar(256) null,
    blob bytea
);

-- Rounds
drop table if exists rounds;
create table rounds (
    id bigserial primary key,
    num integer not null,
    created_at timestamp not null,
    updated_at timestamp not null,
    ends_at timestamp null
);

-- Scores
drop table if exists scores;
create table scores (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    round_id bigint not null references rounds (id),
    scores jsonb
    -- score_predicted float null,
    -- score_actual float null
);

-- Bitmaps
drop table if exists bitmaps;
create table bitmaps (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cbn_id bigint not null references challenge_binary_nodes (id),
    blob bytea
);

-- Fuzzer Stats
drop table if exists fuzzer_stats;
create table fuzzer_stats (
    id bigserial primary key,
    cbn_id bigint not null references challenge_binary_nodes (id),
    created_at timestamp not null,
    updated_at timestamp not null,
    pending_favs int not null,
    pending_total int not null,
    paths_total int null,
    paths_found int null,
    last_path timestamp null
);

-- Function Identities
drop table if exists function_identities;
create table function_identities (
    id bigserial primary key,
    cbn_id bigint not null references challenge_binary_nodes (id),
    created_at timestamp not null,
    updated_at timestamp not null,
    address bigint not null,
    symbol varchar(256) not null
);

-- PCAPs
drop type if exists pcap_type;
create type pcap_type as enum('unknown', 'test', 'crash', 'exploit');

drop table if exists pcaps;
create table pcaps (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cbn_id bigint not null references challenge_binary_nodes (id),
    team_id bigint not null references teams (id),
    round_id bigint not null references rounds (id),
    type pcap_type not null
);

-- CGC Feedbacks
drop table if exists feedbacks;
create table feedbacks (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    round_id bigint not null references rounds (id),
    polls jsonb,
    cbs jsonb,
    povs jsonb
    -- TODO: add raw performance measures
);

-- CGC consensus evaluation
drop table if exists evaluations;
create table evaluations (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    round_id bigint not null references rounds (id),
    team_id bigint not null references teams (id),
    cbs jsonb,
    ids jsonb
    -- TODO: add raw performance measures
);

-- Tester results.
drop table if exists tester_results;
create table tester_results (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    job_id bigint not null references jobs (id),
    error_code int,
    result varchar(256) null,
    stdout_out text,
    stderr_out text,
    performances jsonb
);

-- Round Captured Network Traffic.
drop table if exists raw_round_traffics;
create table raw_round_traffics (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    processed boolean not null,
    round_id bigint not null references rounds (id),
    pickled_data bytea
);

-- Polls Created from Network Traffic for each round
drop table if exists raw_round_polls;
create table raw_round_polls (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cs_id bigint not null references challenge_sets (id),
    sanitized boolean not null,
    round_id bigint not null references rounds (id),
    is_crash boolean not null,
    is_failed boolean not null,
    blob bytea
);

-- Poller results.
drop table if exists valid_polls;
create table valid_polls (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    test_id bigint null references tests (id),
    cs_id bigint not null references challenge_sets (id),
    is_perf_ready boolean not null,
    has_scores_computed boolean not null,
    round_id bigint null references rounds (id),
    blob bytea
);

-- cb tester results.
drop table if exists cb_poll_performances;
create table cb_poll_performances (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cs_id bigint not null references challenge_sets (id),
    patch_type varchar(256) null,
    poll_id bigint not null references valid_polls (id),
    is_poll_ok boolean not null,
    performances jsonb
);

-- Table that stores the reputation of patched CBs
drop table if exists patch_scores;
create table patch_scores (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cs_id bigint not null references challenge_sets (id),
    patch_type varchar(256) null,
    num_polls bigint not null,
    polls_included json null,
    has_failed_polls boolean not null,
    failed_polls jsonb null,
    round_id bigint not null references rounds (id),
    perf_score jsonb
);

-- IDS Rules
drop table if exists ids_rules;
create table ids_rules (
    id bigserial primary key,
    created_at timestamp not null,
    updated_at timestamp not null,
    cs_id bigint not null references challenge_sets (id),
    submitted_at timestamp null,
    rules text
);

commit;
