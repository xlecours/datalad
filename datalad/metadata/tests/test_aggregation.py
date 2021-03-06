# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# -*- coding: utf-8 -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Test metadata aggregation"""


from os.path import join as opj

from datalad.api import metadata
from datalad.api import install
from datalad.distribution.dataset import Dataset


from datalad.tests.utils import skip_ssh
from datalad.tests.utils import with_tree
from datalad.tests.utils import assert_result_count
from datalad.tests.utils import assert_equal
from datalad.tests.utils import assert_not_in
from datalad.tests.utils import assert_dict_equal
from datalad.tests.utils import eq_
from datalad.tests.utils import ok_clean_git
from datalad.tests.utils import skip_direct_mode
from ..extractors.tests.test_bids import bids_template


def _assert_metadata_empty(meta):
    ignore = set(['@id', '@context'])
    assert (not len(meta) or set(meta.keys()) == ignore), \
        'metadata record is not empty: {}'.format(
            {k: meta[k] for k in meta if k not in ignore})


_dataset_hierarchy_template = {
    'origin': {
        'dataset_description.json': """
{
    "Name": "mother_äöü東"
}""",
        'sub': {
            'dataset_description.json': """
{
    "Name": "child_äöü東"
}""",
            'subsub': {
                'dataset_description.json': """
            {
    "Name": "grandchild_äöü東"
}"""}}}}


@with_tree(tree=_dataset_hierarchy_template)
@skip_direct_mode  #FIXME
def test_basic_aggregate(path):
    # TODO give datasets some more metadata to actually aggregate stuff
    base = Dataset(opj(path, 'origin')).create(force=True)
    sub = base.create('sub', force=True)
    #base.metadata(sub.path, init=dict(homepage='this'), apply2global=True)
    subsub = base.create(opj('sub', 'subsub'), force=True)
    base.add('.', recursive=True)
    ok_clean_git(base.path)
    base.aggregate_metadata(recursive=True)
    ok_clean_git(base.path)
    direct_meta = base.metadata(recursive=True, return_type='list')
    # loose the deepest dataset
    sub.uninstall('subsub', check=False)
    # no we should eb able to reaggregate metadata, and loose nothing
    # because we can aggregate aggregated metadata of subsub from sub
    base.aggregate_metadata(recursive=True)
    # same result for aggregate query than for (saved) direct query
    agg_meta = base.metadata(recursive=True, return_type='list')
    for d, a in zip(direct_meta, agg_meta):
        print(d['path'], a['path'])
        assert_dict_equal(d, a)
    # no we can throw away the subdataset tree, and loose no metadata
    base.uninstall('sub', recursive=True, check=False)
    assert(not sub.is_installed())
    ok_clean_git(base.path)
    # same result for aggregate query than for (saved) direct query
    agg_meta = base.metadata(recursive=True, return_type='list')
    for d, a in zip(direct_meta, agg_meta):
        assert_dict_equal(d, a)


# tree puts aggregate metadata structures on two levels inside a dataset
@with_tree(tree={
    '.datalad': {
        'metadata': {
            'objects': {
                'someshasum': '{"homepage": "http://top.example.com"}'},
            'aggregate_v1.json': """\
{
    "sub/deep/some": {
        "dataset_info": "objects/someshasum"
    }
}
"""}},
    'sub': {
        '.datalad': {
            'metadata': {
                'objects': {
                    'someotherhash': '{"homepage": "http://sub.example.com"}'},
                'aggregate_v1.json': """\
{
    "deep/some": {
        "dataset_info": "objects/someotherhash"
    }
}
"""}}},
})
def test_aggregate_query(path):
    ds = Dataset(path).create(force=True)
    # no magic change to actual dataset metadata due to presence of
    # aggregated metadata
    res = ds.metadata(reporton='datasets')
    assert_result_count(res, 1)
    _assert_metadata_empty(res[0]['metadata'])
    # but we can now ask for metadata of stuff that is unknown on disk
    res = ds.metadata(opj('sub', 'deep', 'some'), reporton='datasets')
    assert_result_count(res, 1)
    eq_({'homepage': 'http://top.example.com'}, res[0]['metadata'])
    # and the command will report the aggregated metadata as it is recorded
    # in the dataset that is the closest parent on disk
    ds.create('sub', force=True)
    # same call as above, different result!
    res = ds.metadata(opj('sub', 'deep', 'some'), reporton='datasets')
    assert_result_count(res, 1)
    eq_({'homepage': 'http://sub.example.com'}, res[0]['metadata'])


@with_tree(tree=bids_template)
def test_nested_metadata(path):
    ds = Dataset(path).create(force=True)
    ds.add('.')
    ds.aggregate_metadata()
    # BIDS returns participant info as a nested dict for each file in the
    # content metadata. On the dataset-level this should automatically
    # yield a sequence of participant info dicts, without any further action
    # or BIDS-specific configuration
    meta = ds.metadata('.', reporton='datasets', return_type='item-or-list')['metadata']
    assert_equal(
        meta['datalad_unique_content_properties']['bids']['participant'],
        [
            {
                "age(years)": "20-25",
                "id": "03",
                "gender": "female",
                "handedness": "r",
                "hearing_problems_current": "n",
                "language": "english"
            },
            {
                "age(years)": "30-35",
                "id": "01",
                "gender": "male",
                "handedness": "r",
                "hearing_problems_current": "n",
                "language": u"русский"
            },
        ])
    # we can turn off this kind of auto-summary
    ds.config.add('datalad.metadata.generate-unique-bids', 'false', where='dataset')
    ds.aggregate_metadata()
    meta = ds.metadata('.', reporton='datasets', return_type='item-or-list')['metadata']
    # protect next test a little, in case we enhance our core extractor in the future
    # to provide more info
    if 'datalad_unique_content_properties' in meta:
        assert_not_in('bids', meta['datalad_unique_content_properties'])


# this is for gh-1971
@with_tree(tree=_dataset_hierarchy_template)
@skip_direct_mode  #FIXME
def test_reaggregate_with_unavailable_objects(path):
    base = Dataset(opj(path, 'origin')).create(force=True)
    # force all metadata objects into the annex
    with open(opj(base.path, '.datalad', '.gitattributes'), 'w') as f:
        f.write(
            '** annex.largefiles=nothing\nmetadata/objects/** annex.largefiles=anything\n')
    sub = base.create('sub', force=True)
    subsub = base.create(opj('sub', 'subsub'), force=True)
    base.add('.', recursive=True)
    ok_clean_git(base.path)
    base.aggregate_metadata(recursive=True)
    ok_clean_git(base.path)
    objpath = opj('.datalad', 'metadata', 'objects')
    # weird that it comes out as a string...
    objs = [o for o in sorted(base.repo.find(objpath).split('\n')) if o]
    # we have 3x2 metadata sets (dataset/files) under annex
    eq_(len(objs), 6)
    eq_(all(base.repo.file_has_content(objs)), True)
    # drop all object content
    base.drop(objs, check=False)
    eq_(all(base.repo.file_has_content(objs)), False)
    ok_clean_git(base.path)
    # now re-aggregate, the state hasn't changed, so the file names will
    # be the same
    base.aggregate_metadata(recursive=True)
    eq_(all(base.repo.file_has_content(objs)), True)
    # and there are no new objects
    eq_(
        objs,
        [o for o in sorted(base.repo.find(objpath).split('\n')) if o]
    )


# this is for gh-1987
@skip_ssh
@with_tree(tree=_dataset_hierarchy_template)
@skip_direct_mode  #FIXME
def test_publish_aggregated(path):
    base = Dataset(opj(path, 'origin')).create(force=True)
    # force all metadata objects into the annex
    with open(opj(base.path, '.datalad', '.gitattributes'), 'w') as f:
        f.write(
            '** annex.largefiles=nothing\nmetadata/objects/** annex.largefiles=anything\n')
    base.create('sub', force=True)
    base.add('.', recursive=True)
    ok_clean_git(base.path)
    base.aggregate_metadata(recursive=True)
    ok_clean_git(base.path)

    # create sibling and publish to it
    spath = opj(path, 'remote')
    base.create_sibling(
        name="local_target",
        sshurl="ssh://localhost",
        target_dir=spath)
    base.publish('.', to='local_target', transfer_data='all')
    remote = Dataset(spath)
    objpath = opj('.datalad', 'metadata', 'objects')
    objs = [o for o in sorted(base.repo.find(objpath).split('\n')) if o]
    # all object files a present in both datasets
    eq_(all(base.repo.file_has_content(objs)), True)
    eq_(all(remote.repo.file_has_content(objs)), True)
    # and we can squeeze the same metadata out
    eq_(
        [{k: v for k, v in i.items() if k not in ('path', 'refds', 'parentds')}
         for i in base.metadata('sub')],
        [{k: v for k, v in i.items() if k not in ('path', 'refds', 'parentds')}
         for i in remote.metadata('sub')],
    )


def _get_contained_objs(ds):
    return set(f for f in ds.repo.get_indexed_files()
               if f.startswith(opj('.datalad', 'metadata', 'objects', '')))


def _get_referenced_objs(ds):
    return set([opj('.datalad', 'metadata', r[f])
               for r in ds.metadata(get_aggregates=True)
               for f in ('content_info', 'dataset_info')])


@with_tree(tree=_dataset_hierarchy_template)
@skip_direct_mode  #FIXME
def test_aggregate_removal(path):
    base = Dataset(opj(path, 'origin')).create(force=True)
    # force all metadata objects into the annex
    with open(opj(base.path, '.datalad', '.gitattributes'), 'w') as f:
        f.write(
            '** annex.largefiles=nothing\nmetadata/objects/** annex.largefiles=anything\n')
    sub = base.create('sub', force=True)
    subsub = sub.create(opj('subsub'), force=True)
    base.add('.', recursive=True)
    base.aggregate_metadata(recursive=True)
    ok_clean_git(base.path)
    res = base.metadata(get_aggregates=True)
    assert_result_count(res, 3)
    assert_result_count(res, 1, path=subsub.path)
    # check that we only have object files that are listed in agginfo
    eq_(_get_contained_objs(base), _get_referenced_objs(base))
    # now delete the deepest subdataset to test cleanup of aggregated objects
    # in the top-level ds
    base.remove(opj('sub', 'subsub'), check=False)
    # now aggregation has to detect that subsub is not simply missing, but gone
    # for good
    base.aggregate_metadata(recursive=True)
    ok_clean_git(base.path)
    # internally consistent state
    eq_(_get_contained_objs(base), _get_referenced_objs(base))
    # info on subsub was removed at all levels
    res = base.metadata(get_aggregates=True)
    assert_result_count(res, 0, path=subsub.path)
    assert_result_count(res, 2)
    res = sub.metadata(get_aggregates=True)
    assert_result_count(res, 0, path=subsub.path)
    assert_result_count(res, 1)
